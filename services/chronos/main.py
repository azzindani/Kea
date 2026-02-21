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

from fastapi import FastAPI, HTTPException
from prometheus_client import make_asgi_app
from pydantic import BaseModel, Field

from shared.logging.main import get_logger, setup_logging, LogConfig, RequestLoggingMiddleware
from shared.service_registry import ServiceName, ServiceRegistry
from shared.config import get_settings
from shared.schemas import SuccessResponse

# Import core logic
from services.chronos.core.storage import ensure_schema, load_tasks, save_task, delete_task_db
from services.chronos.core.helpers import next_run
from services.chronos.core.scheduler import scheduler_loop

logger = get_logger(__name__)

# Load settings
settings = get_settings()

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class ScheduleRequest(BaseModel):
    """Create a new scheduled system job."""
    query: str = Field(..., description="System query to run on schedule")
    cron_expr: str = Field(..., description="Cron expression e.g. '0 8 * * *' for 08:00 daily")
    depth: int = Field(default_factory=lambda: get_settings().kernel.default_depth, ge=1, le=get_settings().kernel.max_depth)
    max_steps: int = Field(default_factory=lambda: get_settings().kernel.default_max_steps, ge=1, le=get_settings().kernel.max_steps)
    max_sources: int = Field(default_factory=lambda: get_settings().chronos.default_max_sources)
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
# Lifespan & App
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Initialize DB
    await ensure_schema()
    
    # Start background scheduler
    loop_task = asyncio.create_task(scheduler_loop())
    logger.info("Chronos scheduler started")
    
    yield
    
    # Shutdown
    loop_task.cancel()
    logger.info("Chronos scheduler stopped")


# Initialize standardized logging
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
    return {"status": "ok", "service": "chronos", "timestamp": datetime.now(UTC).isoformat()}


@app.post("/schedule", response_model=SuccessResponse, status_code=get_settings().status_codes.created)
async def create_schedule(req: ScheduleRequest) -> SuccessResponse:
    """Create a new scheduled system job."""
    nxt = next_run(req.cron_expr)
    if nxt is None:
        raise HTTPException(
            status_code=get_settings().status_codes.bad_request, 
            detail=f"Invalid cron expression: {req.cron_expr}"
        )

    task: dict[str, Any] = {
        "task_id": str(uuid.uuid4()),
        "query": req.query,
        "cron_expr": req.cron_expr,
        "depth": req.depth,
        "max_sources": req.max_sources,
        "enabled": req.enabled,
        "created_at": datetime.now(UTC).isoformat(),
        "last_run_at": None,
        "next_run_at": nxt,
    }
    await save_task(task)
    logger.info(f"Chronos: scheduled task {task['task_id']} \u2014 next run {nxt}")
    
    # Format for response
    response_task = {**task}
    response_task["next_run_at"] = nxt.isoformat()
    return SuccessResponse(
        message="Task scheduled successfully",
        data=ScheduledTask(**response_task)
    )


@app.get("/schedule", response_model=list[ScheduledTask])
async def list_schedules() -> list[ScheduledTask]:
    """List all scheduled tasks."""
    rows = await load_tasks()
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
    deleted = await delete_task_db(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api.host,
        port=ServiceRegistry.get_port(ServiceName.CHRONOS)
    )
