"""
Chronos Storage Utilities.

Handles database operations for scheduled tasks.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any

from shared.database.connection import get_database_pool
from shared.logging.main import get_logger
from shared.config import get_settings

logger = get_logger(__name__)

def _get_schema() -> str:
    settings = get_settings()
    return f"""
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    task_id     TEXT PRIMARY KEY,
    query       TEXT NOT NULL,
    cron_expr   TEXT NOT NULL,
    depth       INTEGER NOT NULL DEFAULT {settings.kernel.default_depth},
    max_sources INTEGER NOT NULL DEFAULT {settings.chronos.default_max_sources},
    enabled     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ
);
"""

async def ensure_schema() -> None:
    """Ensure the database schema exists."""
    try:
        pool = await get_database_pool()
        await pool.execute(_get_schema())
    except Exception as e:
        logger.warning(f"Chronos schema init failed: {e}")

async def load_tasks() -> list[dict]:
    """Load all enabled scheduled tasks."""
    try:
        pool = await get_database_pool()
        rows = await pool.fetch("SELECT * FROM scheduled_tasks WHERE enabled = TRUE")
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"Chronos load_tasks failed: {e}")
        return []

async def save_task(task: dict) -> None:
    """Save a new scheduled task."""
    pool = await get_database_pool()
    await pool.execute(
        """
        INSERT INTO scheduled_tasks
            (task_id, query, cron_expr, depth, max_sources, enabled, next_run_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        task["task_id"],
        task["query"],
        task["cron_expr"],
        task["depth"],
        task["max_sources"],
        task["enabled"],
        task.get("next_run_at"),
    )

async def update_last_run(task_id: str, next_run_at: datetime | None) -> None:
    """Update last run time and set next run time."""
    try:
        pool = await get_database_pool()
        await pool.execute(
            "UPDATE scheduled_tasks SET last_run_at = NOW(), next_run_at = $1 WHERE task_id = $2",
            next_run_at,
            task_id,
        )
    except Exception as e:
        logger.warning(f"Chronos update_last_run failed: {e}")

async def delete_task_db(task_id: str) -> bool:
    """Delete a task from the database."""
    try:
        pool = await get_database_pool()
        result = await pool.execute("DELETE FROM scheduled_tasks WHERE task_id = $1", task_id)
        return result == "DELETE 1"
    except Exception as e:
        logger.warning(f"Chronos delete_task failed: {e}")
        return False
