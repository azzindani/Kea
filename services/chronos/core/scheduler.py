"""
Chronos Scheduler Engine.

Handles the polling loop and task execution (firing).
"""

from __future__ import annotations
import asyncio
import httpx

from shared.logging.main import get_logger
from shared.service_registry import ServiceName, ServiceRegistry
from shared.config import get_settings
from services.chronos.core.storage import load_tasks, update_last_run
from services.chronos.core.helpers import is_due, next_run

logger = get_logger(__name__)

async def fire_task(task: dict) -> None:
    """POST to Orchestrator /execute for a scheduled task."""
    settings = get_settings()
    orch_url = ServiceRegistry.get_url(ServiceName.ORCHESTRATOR)
    
    payload = {
        "query": task["query"],
        "depth": task.get("depth", settings.jobs.default_depth),
        "max_sources": task.get("max_sources", settings.chronos.default_max_sources),
    }
    
    try:
        async with httpx.AsyncClient(timeout=settings.timeouts.long) as client:
            resp = await client.post(f"{orch_url}/execute", json=payload)
            if resp.status_code == 200:
                logger.info(
                    f"Chronos: fired task {task['task_id']} \u2192 job_id={resp.json().get('job_id')}"
                )
            else:
                logger.warning(f"Chronos: task {task['task_id']} fire returned {resp.status_code}")
    except Exception as e:
        logger.error(f"Chronos: failed to fire task {task['task_id']}: {e}")

async def scheduler_loop() -> None:
    """Poll according to config and fire any due tasks."""
    settings = get_settings()
    
    while True:
        try:
            tasks = await load_tasks()
            for task in tasks:
                if is_due(task.get("next_run_at")):
                    # Fire task in background
                    asyncio.create_task(fire_task(task))
                    
                    # Update status in DB
                    new_next_run = next_run(task["cron_expr"])
                    await update_last_run(task["task_id"], new_next_run)
        except Exception as e:
            logger.error(f"Chronos scheduler loop error: {e}")
            
        await asyncio.sleep(settings.chronos.poll_interval)

