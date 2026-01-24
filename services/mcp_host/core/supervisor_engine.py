"""
Supervisor Engine (The Factory Manager).

Monitors system resources (RAM/CPU) and dispatches tasks from the `micro_tasks` queue
based on available capacity and task priority.
"""
import asyncio
import time
import psutil
from collections import deque

from shared.logging import get_logger

logger = get_logger(__name__)

# ============================================================================
# Governance Policies (The Corporate Budget)
# ============================================================================
# ============================================================================
# Governance Policies (Loaded from Config)
# ============================================================================
from shared.config import get_settings


class SupervisorEngine:
    """
    Traffic controller for the MCP Host.
    Replaces blind 'asyncio.gather' with a governed loop.
    """
    
    def __init__(self):
        self._running = False
        self._current_load = 0
        self._active_tasks: dict[str, int] = {} # task_id -> cost
        self._hardware_paused = False # State tracker for logging
        
        from shared.dispatcher import get_dispatcher
        from services.mcp_host.core.session_registry import get_session_registry
        
        self.dispatcher = get_dispatcher()
        self.registry = get_session_registry()
        
    async def start(self):
        """Start the supervisor loop."""
        if self._running:
            return
            
        self._running = True
        logger.info("👮 Supervisor Engine Started to govern execution.")
        
        # Ensure DB schema exists before polling
        try:
             await self.dispatcher.ensure_schema()
        except Exception as e:
             logger.warning(f"Supervisor could not ensure schema (DB might be down): {e}")

        asyncio.create_task(self._supervisor_loop())

    async def _supervisor_loop(self):
        """The main governance loop."""
        while self._running:
            try:
                # 1. Check Hardware Health (The Pulse)
                if not self._check_hardware():
                    await asyncio.sleep(5)
                    continue

                # 2. Check Capacity
                config = get_settings()
                max_cost = config.governance.max_concurrent_cost
                
                # Recalculate load just in case
                self._current_load = sum(self._active_tasks.values())
                available_capacity = max_cost - self._current_load
                
                if available_capacity <= 0:
                    # Factory Full
                    await asyncio.sleep(config.governance.poll_interval)
                    continue

                # 3. Fetch Next Task (Highest Priority, Fits in Budget)
                task = await self._fetch_next_task(max_cost=available_capacity)
                
                if task:
                    # 4. Spawn Worker
                    task_id = str(task['task_id'])
                    cost = task['resource_cost']
                    tool_name = task['tool_name']
                    
                    self._active_tasks[task_id] = cost
                    asyncio.create_task(self._run_worker(task))
                    
                    logger.info(f"🚀 Spawning {tool_name} (Cost: {cost}, Load: {self._current_load + cost}/{max_cost})")
                else:
                    # No tasks fit capability or queue empty
                    await asyncio.sleep(2)
                    
            except Exception as e:
                logger.error(f"Supervisor Loop Error: {e}")
                await asyncio.sleep(5)

    def _check_hardware(self) -> bool:
        """Return True if hardware is healthy enough to spawn tasks."""
        config = get_settings()
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        
        # Get hardware profile for advanced OOM checks
        vram_percent = 0.0
        ram_oom_risk = False
        try:
            from shared.hardware.detector import detect_hardware
            hw = detect_hardware()
            
            # Refresh and check RAM OOM risk
            hw.refresh_ram()
            ram_oom_risk = hw.is_ram_oom_risk(required_gb=2.0)
            
            # Refresh and check VRAM
            if hw.cuda_available:
                hw.refresh_vram()
                vram_percent = hw.vram_pressure() * 100
        except Exception:
            pass
        
        is_critical = False
        
        # RAM OOM check - use the more accurate is_ram_oom_risk method
        if ram_oom_risk or ram > config.governance.max_ram_percent:
            if not self._hardware_paused:
                available_gb = getattr(hw, 'ram_available_gb', 0)
                logger.warning(f"⚠️ RAM Critical ({ram}% used, {available_gb:.1f}GB free). Pausing.")
            is_critical = True
            
        elif cpu > config.governance.max_cpu_percent and vram_percent < 80:
             # Only pause if BOTH CPU is high AND GPU isn't available/loaded
             # If GPU is available and has capacity, let GPU tasks proceed
             if not self._hardware_paused:
                  logger.warning(f"⚠️ CPU Critical ({cpu}% > {config.governance.max_cpu_percent}%). Pausing dispatch.")
             is_critical = True
        
        # Add VRAM check for GPU OOM prevention
        if vram_percent > 90:
            if not self._hardware_paused:
                logger.warning(f"⚠️ VRAM Critical ({vram_percent:.1f}% > 90%). Pausing GPU tasks.")
            is_critical = True
        
        # State Transition Logic
        if is_critical and not self._hardware_paused:
            self._hardware_paused = True
        elif not is_critical and self._hardware_paused:
            self._hardware_paused = False
            logger.info(f"✅ Hardware recovered (CPU: {cpu}%, RAM: {ram}%, VRAM: {vram_percent:.1f}%). Resuming dispatch.")
            
        return not is_critical

    async def _fetch_next_task(self, max_cost: int):
        """Get the highest priority task that fits in the budget."""
        # Using SKIP LOCKED to avoid race conditions with other replicas (if any)
        # We look for pending tasks OR queued tasks
        
        from shared.database.connection import get_database_pool as get_db_pool
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Simple greedy fetch
            row = await conn.fetchrow("""
                UPDATE micro_tasks
                SET status = 'processing', updated_at = (NOW() AT TIME ZONE 'utc')
                WHERE task_id = (
                    SELECT task_id
                    FROM micro_tasks
                    WHERE status = 'pending'
                    AND resource_cost <= $1
                    AND (locked_until IS NULL OR locked_until < (NOW() AT TIME ZONE 'utc'))
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING task_id, tool_name, parameters::text as params_text, resource_cost, retry_count, max_retries
            """, max_cost)
            
            if row:
                # Convert back to dict
                import json
                data = dict(row)
                data['parameters'] = json.loads(data['params_text'])
                return data
            return None

    async def _run_worker(self, task_data: dict):
        """Execute the task with retry logic."""
        task_id = str(task_data['task_id'])
        tool_name = task_data['tool_name']
        args = task_data['parameters']
        retry_count = task_data['retry_count']
        max_retries = task_data['max_retries']
        
        try:
            # 1. Resolve Server
            # Try to get server from registry RAM
            server_name = self.registry.get_server_for_tool(tool_name)
            
            if not server_name:
                # 2. Lazy Discovery (Intelligence)
                # If we don't know the tool, scan headers/files again (non-blocking if possible, but here we block)
                # Since this is a worker, blocking 1-2s is acceptable for "JIT Discovery" of new tools
                await self.registry.list_all_tools()
                server_name = self.registry.get_server_for_tool(tool_name)
            
            if not server_name:
                 raise ValueError(f"Tool {tool_name} not found in Registry.")

            # 3. Get Session (JIT Spawn happens here)
            session = await self.registry.get_session(server_name)
            
            # 4. EXECUTE
            result = await session.call_tool(tool_name, args)
            
            # Extract content
            content_str = "\n".join([c.text for c in result.content if getattr(c, 'text', None)])
            status = "done"
            error_log = None
            if result.isError:
                raise Exception(content_str)

            # SUCCESS
            await self._update_task_status(task_id, 'done', result_summary=content_str[:500])
            
        except Exception as e:
            # FAILURE & RETRY
            logger.warning(f"Task {task_id} failed: {e}")
            
            if retry_count < max_retries:
                # Schedule Retry (Exponential Backoff)
                wait_seconds = 2 ** (retry_count + 1)
                logger.info(f"🔄 Rescheduling task {task_id} in {wait_seconds}s")
                await self._schedule_retry(task_id, retry_count + 1, wait_seconds, str(e))
            else:
                # Dead Letter
                logger.error(f"❌ Task {task_id} dead after {max_retries} retries.")
                await self._update_task_status(task_id, 'error', error_log=str(e))
                
        finally:
            # Release Resources
            if task_id in self._active_tasks:
                del self._active_tasks[task_id]

    async def _update_task_status(self, task_id: str, status: str, result_summary: str = None, error_log: str = None):
        from shared.database.connection import get_database_pool as get_db_pool
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE micro_tasks 
                SET status = $1, result_summary = $2, error_log = $3, updated_at = (NOW() AT TIME ZONE 'utc')
                WHERE task_id = $4
            """, status, result_summary, error_log, task_id)
            
            # Check batch completion
            # (Optimization: We could do this less frequently or async)
            batch_id = await conn.fetchval("SELECT batch_id FROM micro_tasks WHERE task_id = $1", task_id)
            if batch_id:
                await self.dispatcher.complete_batch_if_done(str(batch_id))

    async def _schedule_retry(self, task_id: str, new_retry_count: int, delay_seconds: int, error_log: str):
        from shared.database.connection import get_database_pool as get_db_pool
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE micro_tasks 
                SET status = 'pending',
                    retry_count = $1,
                    locked_until = (NOW() AT TIME ZONE 'utc') + make_interval(secs => $2),
                    error_log = $3,
                    updated_at = (NOW() AT TIME ZONE 'utc')
                WHERE task_id = $4
            """, new_retry_count, float(delay_seconds), error_log, task_id)


# Singleton
_supervisor: SupervisorEngine | None = None

def get_supervisor() -> SupervisorEngine:
    global _supervisor
    if _supervisor is None:
        _supervisor = SupervisorEngine()
    return _supervisor
