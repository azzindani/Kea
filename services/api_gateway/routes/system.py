"""
System API Routes.

Endpoints for system status, health, and configuration.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from shared.config import get_settings
from shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ============================================================================
# Models
# ============================================================================


class SystemHealth(BaseModel):
    """System health response."""

    status: str
    version: str
    environment: str
    uptime_seconds: float


class SystemCapabilities(BaseModel):
    """System capabilities response."""

    mcp_servers: list[str]
    research_paths: list[str]
    llm_providers: list[str]
    max_parallel_tools: int


# ============================================================================
# Routes
# ============================================================================

_start_time = datetime.utcnow()


@router.get("/health", response_model=SystemHealth)
async def system_health():
    """Get system health status."""
    settings = get_settings()
    uptime = (datetime.utcnow() - _start_time).total_seconds()

    return SystemHealth(
        status="healthy",
        version=settings.app.version,
        environment=settings.environment.value,
        uptime_seconds=uptime,
    )


@router.get("/capabilities", response_model=SystemCapabilities)
async def system_capabilities():
    """Get system capabilities and feature flags."""
    settings = get_settings()

    return SystemCapabilities(
        mcp_servers=[s.name for s in settings.mcp.servers if s.enabled],
        research_paths=["deep_research"],
        llm_providers=["openrouter"],
        max_parallel_tools=settings.mcp.max_concurrent_tools,
    )


@router.get("/config")
async def get_config():
    """Get current configuration (non-sensitive)."""
    settings = get_settings()

    return {
        "environment": settings.environment.value,
        "llm": {
            "provider": settings.llm.default_provider,
            "model": settings.llm.default_model,
            "temperature": settings.llm.temperature,
        },
        "logging": {
            "level": settings.logging.level,
            "format": settings.logging.format,
        },
    }


@router.get("/metrics/summary")
async def metrics_summary() -> dict:
    """Get high-level metrics summary from the database."""
    try:
        from shared.database.connection import get_database_pool

        pool = await get_database_pool()
        total_jobs = await pool.fetchval("SELECT COUNT(*) FROM research_jobs") or 0
        total_tool_calls = 0  # To be implemented with new telemetry standard
        avg_duration = await pool.fetchval(
            """
            SELECT AVG(EXTRACT(EPOCH FROM (updated_at - created_at)))
            FROM research_jobs
            WHERE status = 'completed' AND updated_at IS NOT NULL
            """
        )
        return {
            "total_jobs": int(total_jobs),
            "total_tool_calls": int(total_tool_calls),
            "total_tokens_used": 0,  # approximated; tracked via LLM usage route
            "avg_job_duration_seconds": round(float(avg_duration), 2) if avg_duration else 0.0,
        }
    except Exception as exc:
        logger.warning(f"Metrics query failed: {exc}")
        return {
            "total_jobs": 0,
            "total_tool_calls": 0,
            "total_tokens_used": 0,
            "avg_job_duration_seconds": 0.0,
        }
