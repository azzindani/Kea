"""
Resource Governor ("The Foreman").

Strictly controls system load by gating new agent spawns based on:
1. System Metrics (CPU/RAM)
2. Active Agent Count
3. Postgres Connection Pool Status
"""
from __future__ import annotations

import asyncio
import os
import psutil
from dataclasses import dataclass
from typing import Literal

from shared.logging import get_logger
from shared.database.connection import get_db_pool

logger = get_logger(__name__)


@dataclass
class SystemState:
    """Current system health state."""
    cpu_percent: float
    ram_percent: float
    active_agents: int
    db_connections: int
    status: Literal["HEALTHY", "WARNING", "CRITICAL"]


class ResourceGovernor:
    """
    Forces system stability by denying work when overloaded.
    """
    
    def __init__(self):
        # Limits
        self.MAX_CPU = float(os.getenv("MAX_CPU_PERCENT", "80.0"))
        self.MAX_RAM = float(os.getenv("MAX_RAM_PERCENT", "80.0"))
        self.MAX_AGENTS = int(os.getenv("MAX_CONCURRENT_AGENTS", "50"))
        
        # State
        self._last_state: SystemState | None = None
        
        # Prime CPU stats
        psutil.cpu_percent(interval=None)
        
    async def get_system_state(self) -> SystemState:
        """Alias for check_health to match public API expectations."""
        return await self.check_health()

    @property
    def _active_agents(self) -> int:
        """Return the active agent count from the last health check."""
        if self._last_state:
            return self._last_state.active_agents
        return 0

    async def check_health(self) -> SystemState:
        """Get current system health snapshot."""
        # 1. Hardware Metrics
        from shared.hardware.detector import detect_hardware
        profile = detect_hardware()
        
        cpu = psutil.cpu_percent(interval=None)
        ram = profile.memory_pressure() * 100
        
        # 2. Db / Agent Metrics
        pool = await get_db_pool()
        active_agents = 0
        db_conns = 0
        
        try:
            async with pool.acquire() as conn:
                # Approximate active agents by counting processing jobs in micro_tasks (v4 Core)
                # Fallback to 0 if table doesn't exist yet
                try:
                    active_agents = await conn.fetchval("""
                        SELECT COUNT(*) FROM micro_tasks 
                        WHERE status = 'processing'
                    """) or 0
                except Exception:
                    # Table might not be created yet if no tasks have run
                    active_agents = 0
                
                # DB Connections
                db_conns = await conn.fetchval("SELECT count(*) FROM pg_stat_activity")
        except Exception as e:
            logger.error(f"Failed to fetch DB metrics: {e}")
            
        status = "HEALTHY"
        if cpu > self.MAX_CPU or ram > self.MAX_RAM or active_agents >= self.MAX_AGENTS:
            status = "CRITICAL"
        elif cpu > (self.MAX_CPU * 0.8) or ram > (self.MAX_RAM * 0.8):
            status = "WARNING"
            
        self._last_state = SystemState(
            cpu_percent=cpu,
            ram_percent=ram,
            active_agents=active_agents,
            db_connections=db_conns,
            status=status
        )
        return self._last_state

    async def can_spawn_agent(self, requested_count: int = 1) -> bool:
        """
        Gatekeeper for new agents.
        Returns True if system can handle load, False otherwise.
        """
        state = await self.check_health()
        
        if state.status == "CRITICAL":
            logger.warning(
                f"GOVERNOR: DENIED spawn. CPU:{state.cpu_percent}% RAM:{state.ram_percent}% "
                f"Agents:{state.active_agents}/{self.MAX_AGENTS}"
            )
            return False
            
        if state.active_agents + requested_count > self.MAX_AGENTS:
            logger.warning(
                f"GOVERNOR: DENIED spawn. Agents limit reached: "
                f"{state.active_agents}+{requested_count} > {self.MAX_AGENTS}"
            )
            return False
            
        logger.debug(f"GOVERNOR: APPROVED spawn. System healthy.")
        return True


# Global Instance
_governor: ResourceGovernor | None = None

def get_governor() -> ResourceGovernor:
    global _governor
    if _governor is None:
        _governor = ResourceGovernor()
    return _governor
