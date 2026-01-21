"""
Background Swarm Execution.

Runs tasks from the `micro_tasks` table in parallel.
"""
import asyncio
import json
from services.mcp_host.core.tool_manager import get_mcp_orchestrator
from shared.dispatcher import get_dispatcher
from shared.logging import get_logger

logger = get_logger(__name__)


async def run_swarm_batch(batch_id: str, tasks: list[dict]):
    """
    Execute a batch of tasks in parallel (Fire and Forget).
    This runs in BackgroundTasks.
    """
    logger.info(f"🚀 Starting Swarm Batch {batch_id} ({len(tasks)} tasks)")
    
    orchestrator = get_mcp_orchestrator()
    dispatcher = get_dispatcher()
    
    async def execute_single_task(task_def):
        tool_name = task_def["tool_name"]
        args = task_def["arguments"]
        
        # Mark processing (Optional, skipping for speed/simplicity as 'pending' covers it)
        
        try:
            # 1. Run Tool
            result = await orchestrator.call_tool(tool_name, args)
            
            # 2. Extract Artifact ID if present (Standardized Output)
            # Assuming result.content is list of objects, we grab text
            content_str = "\n".join([c.text for c in result.content if getattr(c, 'text', None)])
            
            status = "done"
            error_log = None
            if result.isError:
                status = "error"
                error_log = content_str
            
            # 3. Update DB
            await dispatcher.update_task(
                batch_id=batch_id,
                tool_name=tool_name,
                arguments=args,
                status=status,
                result_summary=content_str[:500], # Keep concise in DB
                error_log=error_log
                # artifact_id? Need to parse or change tool to return it.
                # For now, if the tool SAVES to Vault, it should return artifact_id in text.
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
