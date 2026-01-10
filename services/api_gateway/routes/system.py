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
        version="0.1.0",
        environment=settings.environment.value,
        uptime_seconds=uptime,
    )


@router.get("/capabilities", response_model=SystemCapabilities)
async def system_capabilities():
    """Get system capabilities and feature flags."""
    settings = get_settings()
    
    return SystemCapabilities(
        mcp_servers=[s.name for s in settings.mcp.servers if s.enabled],
        research_paths=["memory_fork", "shadow_lab", "grand_synthesis", "deep_research"],
        llm_providers=["openrouter"],
        max_parallel_tools=settings.research.parallel_tools,
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
        "research": {
            "max_depth": settings.research.max_depth,
            "max_sources": settings.research.max_sources,
            "parallel_tools": settings.research.parallel_tools,
        },
        "logging": {
            "level": settings.logging.level,
            "format": settings.logging.format,
        },
    }


@router.get("/metrics/summary")
async def metrics_summary():
    """Get high-level metrics summary."""
    return {
        "total_jobs": 0,
        "total_tool_calls": 0,
        "total_tokens_used": 0,
        "avg_job_duration_seconds": 0.0,
    }
