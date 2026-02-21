"""
Chronos — Scheduling Service.

Manages recurring and one-shot system jobs via cron expressions.
Persists scheduled tasks in PostgreSQL and fires them by POSTing to
the Orchestrator's /execute endpoint.
"""

from __future__ import annotations

import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from prometheus_client import make_asgi_app
from pydantic import BaseModel, Field

from shared.logging.main import get_logger, setup_logging, LogConfig, RequestLoggingMiddleware
from shared.service_registry import ServiceName, ServiceRegistry
from shared.config import get_settings

# Initialize standardized logging
# (Moved below settings loading)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


class ScheduleRequest(BaseModel):
    """Create a new scheduled system job."""
    _settings = get_settings()

    query: str = Field(..., description="System query to run on schedule")
    cron_expr: str = Field(..., description="Cron expression e.g. '0 8 * * *' for 08:00 daily")
    depth: int = Field(default=_settings.kernel.default_depth, ge=1, le=_settings.kernel.max_depth)
    max_steps: int = Field(default=_settings.kernel.default_max_steps, ge=1, le=_settings.kernel.max_steps)
    enabled: bool = Field(default=True)


class ScheduledTask(BaseModel):
    """A scheduled task as stored in DB."""
    task_id: str
    query: str
    cron_expr: str
    depth: int
    max_sources: int
    enabled: bool
    created_at: str
    last_run_at: str | None
    next_run_at: str | None


# ---------------------------------------------------------------------------
# Storage (PostgreSQL)
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    task_id     TEXT PRIMARY KEY,
    query       TEXT NOT NULL,
    cron_expr   TEXT NOT NULL,
    depth       INTEGER NOT NULL DEFAULT 2,
    max_sources INTEGER NOT NULL DEFAULT 10,
    enabled     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ
);
"""


async def _ensure_schema() -> None:
    try:
        from shared.database.connection import get_database_pool

        pool = await get_database_pool()
        await pool.execute(_SCHEMA)
    except Exception as e:
        logger.warning(f"Chronos schema init failed: {e}")


async def _load_tasks() -> list[dict]:
    try:
        from shared.database.connection import get_database_pool

        pool = await get_database_pool()
        rows = await pool.fetch("SELECT * FROM scheduled_tasks WHERE enabled = TRUE")
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"Chronos load_tasks failed: {e}")
        return []


async def _save_task(task: dict) -> None:
    from shared.database.connection import get_database_pool

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


async def _update_last_run(task_id: str, next_run_at: datetime | None) -> None:
    try:
        from shared.database.connection import get_database_pool

        pool = await get_database_pool()
        await pool.execute(
            "UPDATE scheduled_tasks SET last_run_at = NOW(), next_run_at = $1 WHERE task_id = $2",
            next_run_at,
            task_id,
        )
    except Exception as e:
        logger.warning(f"Chronos update_last_run failed: {e}")


async def _delete_task(task_id: str) -> bool:
    try:
        from shared.database.connection import get_database_pool

        pool = await get_database_pool()
        result = await pool.execute("DELETE FROM scheduled_tasks WHERE task_id = $1", task_id)
        return result == "DELETE 1"
    except Exception as e:
        logger.warning(f"Chronos delete_task failed: {e}")
        return False


# ---------------------------------------------------------------------------
# Cron helpers
# ---------------------------------------------------------------------------


def _next_run(cron_expr: str) -> datetime | None:
    """Compute the next UTC run time for a cron expression."""
    try:
        from croniter import croniter

        now = datetime.now(UTC)
        return croniter(cron_expr, now).get_next(datetime)
    except Exception as e:
        logger.warning(f"Invalid cron expression '{cron_expr}': {e}")
        return None


def _is_due(next_run_at: Any, tolerance_s: float | None = None) -> bool:
    """Return True if the task is due to fire (within tolerance seconds)."""
    if tolerance_s is None:
        tolerance_s = settings.chronos.due_tolerance
    if next_run_at is None:
        return False
    if isinstance(next_run_at, str):
        next_run_at = datetime.fromisoformat(next_run_at)
    if next_run_at.tzinfo is None:
        next_run_at = next_run_at.replace(tzinfo=UTC)
    now = datetime.now(UTC)
    return now >= next_run_at - __import__("datetime").timedelta(seconds=tolerance_s)


# ---------------------------------------------------------------------------
# Scheduler loop
# ---------------------------------------------------------------------------


async def _fire_task(task: dict) -> None:
    """POST to Orchestrator /execute for a scheduled task."""
    orch_url = ServiceRegistry.get_url(ServiceName.ORCHESTRATOR)
    payload = {
        "query": task["query"],
        "depth": task.get("depth", 2),
        "max_sources": task.get("max_sources", 10),
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


async def _scheduler_loop() -> None:
    """Poll every 60 seconds and fire any due tasks."""
    while True:
        try:
            tasks = await _load_tasks()
            for task in tasks:
                if _is_due(task.get("next_run_at")):
                    asyncio.create_task(_fire_task(task))
                    next_run = _next_run(task["cron_expr"])
                    await _update_last_run(task["task_id"], next_run)
        except Exception as e:
            logger.error(f"Chronos scheduler loop error: {e}")
        await asyncio.sleep(settings.chronos.poll_interval)


# ---------------------------------------------------------------------------
# Lifespan & App
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await _ensure_schema()
    loop_task = asyncio.create_task(_scheduler_loop())
    logger.info("Chronos scheduler started")
    yield
    loop_task.cancel()
    logger.info("Chronos scheduler stopped")


# Load settings
settings = get_settings()

setup_logging(LogConfig(
    level=settings.logging.level,
    service_name="chronos",
))

app = FastAPI(
    title=f"{settings.app.name} - Chronos",
    description="Recurring and one-shot system job management",
    version=settings.app.version,
    lifespan=lifespan,
)
app.add_middleware(RequestLoggingMiddleware)
app.mount("/metrics", make_asgi_app())


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "chronos"}


@app.post("/schedule", response_model=ScheduledTask, status_code=201)
async def create_schedule(req: ScheduleRequest) -> ScheduledTask:
    """Create a new scheduled system job."""
    next_run = _next_run(req.cron_expr)
    if next_run is None:
        raise HTTPException(status_code=400, detail=f"Invalid cron expression: {req.cron_expr}")

    task: dict[str, Any] = {
        "task_id": str(uuid.uuid4()),
        "query": req.query,
        "cron_expr": req.cron_expr,
        "depth": req.depth,
        "max_sources": req.max_sources,
        "enabled": req.enabled,
        "created_at": datetime.now(UTC).isoformat(),
        "last_run_at": None,
        "next_run_at": next_run,
    }
    await _save_task(task)
    logger.info(f"Chronos: scheduled task {task['task_id']} \u2014 next run {next_run}")
    return ScheduledTask(**{**task, "next_run_at": next_run.isoformat()})


@app.get("/schedule", response_model=list[ScheduledTask])
async def list_schedules() -> list[ScheduledTask]:
    """List all scheduled tasks."""
    rows = await _load_tasks()
    result = []
    for r in rows:
        result.append(
            ScheduledTask(
                task_id=r["task_id"],
                query=r["query"],
                cron_expr=r["cron_expr"],
                depth=r["depth"],
                max_sources=r["max_sources"],
                enabled=r["enabled"],
                created_at=r["created_at"].isoformat()
                if hasattr(r["created_at"], "isoformat")
                else str(r["created_at"]),
                last_run_at=r["last_run_at"].isoformat() if r.get("last_run_at") else None,
                next_run_at=r["next_run_at"].isoformat() if r.get("next_run_at") else None,
            )
        )
    return result


@app.delete("/schedule/{task_id}", status_code=204)
async def delete_schedule(task_id: str) -> None:
    """Delete a scheduled task."""
    deleted = await _delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


if __name__ == "__main__":
    import uvicorn
    from shared.service_registry import ServiceRegistry, ServiceName

    uvicorn.run(
        app,
        host=settings.api.host,
        port=ServiceRegistry.get_port(ServiceName.CHRONOS)
    )
