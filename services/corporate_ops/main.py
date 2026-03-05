"""
Corporate Operations Service — Main Entrypoint.

FastAPI application for the Tier 8 Corporation Kernel's HTTP service.
Exposes workforce management, mission orchestration, and quality
assessment endpoints.

Port: 8011 (configured in shared/config.py → services.corporate_ops)
"""

from __future__ import annotations

import sys
import asyncio
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.config import get_settings
from shared.environment import get_environment_config
from shared.logging.main import (
    LogConfig,
    RequestLoggingMiddleware,
    get_logger,
    set_system_info,
    setup_logging,
)

from services.corporate_ops.routers import (
    orchestration,
    quality,
    workforce,
)

log = get_logger(__name__)


# ============================================================================
# Lifespan
# ============================================================================


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan manager."""
    settings = get_settings()
    env_config = get_environment_config()

    # Setup logging
    setup_logging(
        LogConfig(
            level=settings.logging.level,
            format=settings.logging.format,
            service_name="corporate_ops",
        )
    )

    set_system_info(version=settings.app.version, environment=env_config.mode.value)

    log.info(
        f"Corporate Operations Service {settings.app.version} started [{env_config.mode.value}]"
    )

    yield

    # Cleanup clients
    from services.corporate_ops.clients.orchestrator_client import (
        get_corporate_orchestrator_client,
    )

    try:
        client = await get_corporate_orchestrator_client()
        await client.close()
    except Exception:
        pass

    log.info("Corporate Operations Service stopped")


# ============================================================================
# App Factory
# ============================================================================

settings = get_settings()

app = FastAPI(
    title="Corporate Operations Service",
    description="Tier 8 Corporation Kernel — Workforce, Orchestration, Quality",
    version=settings.app.version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================================
# Middleware
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)


# ============================================================================
# Exception Handlers
# ============================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    env_config = get_environment_config()
    log.error(f"Unhandled exception: {exc}", exc_info=True)

    if env_config.is_development:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error": str(exc),
                "traceback": traceback.format_exc().split("\n"),
            },
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ============================================================================
# Routers
# ============================================================================

app.include_router(
    workforce.router, prefix="/api/v1/workforce", tags=["Workforce"]
)
app.include_router(
    orchestration.router, prefix="/api/v1/orchestration", tags=["Orchestration"]
)
app.include_router(
    quality.router, prefix="/api/v1/quality", tags=["Quality"]
)


# ============================================================================
# Root Routes
# ============================================================================


@app.get("/")
async def root():
    """Service root."""
    settings = get_settings()
    env_config = get_environment_config()
    return {
        "name": "Corporate Operations Service",
        "version": settings.app.version,
        "tier": 8,
        "environment": env_config.mode.value,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "ok",
        "service": "corporate_ops",
    }


@app.get("/health/full")
async def full_health_check():
    """Comprehensive health check — validates connectivity to dependencies."""
    from services.corporate_ops.clients.orchestrator_client import (
        get_corporate_orchestrator_client,
    )

    status = {"orchestrator": "unknown", "vault": "unknown"}

    # Check Orchestrator
    try:
        orch = await get_corporate_orchestrator_client()
        orch_health = await asyncio.wait_for(
            orch._request("GET", "/health"), timeout=5.0
        )
        status["orchestrator"] = "ok" if orch_health.status_code == 200 else "degraded"
    except Exception:
        status["orchestrator"] = "unreachable"

    overall = "ok" if all(v == "ok" for v in status.values()) else "degraded"

    return {
        "status": overall,
        "service": "corporate_ops",
        "dependencies": status,
    }


# ============================================================================
# Main
# ============================================================================

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def main():
    """Run the Corporate Operations service."""
    import uvicorn

    settings = get_settings()
    from shared.service_registry import ServiceName, ServiceRegistry

    uvicorn.run(
        "services.corporate_ops.main:app",
        host=settings.api.host,
        port=ServiceRegistry.get_port(ServiceName.CORPORATE_OPS),
        reload=settings.is_development,
        workers=settings.api.workers_dev if settings.is_development else settings.api.workers_prod,
    )


if __name__ == "__main__":
    main()
