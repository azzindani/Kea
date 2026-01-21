"""
Background Swarm Execution.

Runs tasks from the `micro_tasks` table in parallel.
"""
import asyncio
import json

from shared.dispatcher import get_dispatcher
from shared.logging import get_logger

logger = get_logger(__name__)


async def run_swarm_batch(batch_id: str, tasks: list[dict]):
    """
    Execute a batch of tasks in parallel (Fire and Forget).
    This runs in BackgroundTasks.
    """
    logger.info(f"🚀 Starting Swarm Batch {batch_id} ({len(tasks)} tasks)")
    
    from services.mcp_host.core.session_registry import get_session_registry
    registry = get_session_registry()
    dispatcher = get_dispatcher()
    
    async def execute_single_task(task_def):
        tool_name = task_def["tool_name"]
        args = task_def["arguments"]
        
        try:
            # 1. Resolve Server
            server_name = registry.get_server_for_tool(tool_name)
            if not server_name:
                await registry.list_all_tools()
                server_name = registry.get_server_for_tool(tool_name)
            
            if not server_name:
                raise ValueError(f"Tool {tool_name} not found in Registry.")

            # 2. Execute
            session = await registry.get_session(server_name)
            result = await session.call_tool(tool_name, args)
            
            # 3. Extract output
            content_str = "\n".join([c.text for c in result.content if getattr(c, 'text', None)])
            
            status = "done"
            error_log = None
            if result.isError:
                status = "error"
                error_log = content_str
            
            # 4. Update DB
            await dispatcher.update_task(
                batch_id=batch_id,
                tool_name=tool_name,
                arguments=args,
                status=status,
                result_summary=content_str[:500],
                error_log=error_log
            )
            
        except Exception as e:
            logger.error(f"Task failed: {e}")
            await dispatcher.update_task(
                batch_id=batch_id,
                tool_name=tool_name,
                arguments=args,
                status="error",
                error_log=str(e)
            )

    # Fan-Out
    await asyncio.gather(*[execute_single_task(t) for t in tasks])
    
    # Complete
    await dispatcher.complete_batch_if_done(batch_id)
    logger.info(f"✅ Swarm Batch {batch_id} completed")
