"""
Corporate Gateway Service.

Tier 9 — THE FastAPI entry point for the entire Corporation Kernel.
One service, one entry point, one API: POST /corporate/process.
"""

from __future__ import annotations

import asyncio
import sys
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

from services.corporate_gateway.routers import corporate

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan manager."""
    app_settings = get_settings()
    env_config = get_environment_config()

    setup_logging(
        LogConfig(
            level=app_settings.logging.level,
            format=app_settings.logging.format,
            service_name="corporate_gateway",
        )
    )

    set_system_info(
        version=app_settings.app.version,
        environment=env_config.mode.value,
    )

    log.info(
        "corporate_gateway_started",
        version=app_settings.app.version,
        env=env_config.mode.value,
    )

    yield

    log.info("corporate_gateway_stopped")


settings = get_settings()

app = FastAPI(
    title="Corporate Gateway Service",
    description=(
        "Tier 9 — Corporation Kernel Apex. "
        "One service, one entry point: POST /corporate/process."
    ),
    version=settings.app.version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)


# --- Exception handlers ---
@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    env_config = get_environment_config()
    log.error("unhandled_exception", error=str(exc), exc_info=True)

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


# --- Routers ---
app.include_router(
    corporate.router,
    prefix="/corporate",
    tags=["Corporate"],
)


# --- Health & Root ---
@app.get("/")
async def root():
    """Service root."""
    app_settings = get_settings()
    env_config = get_environment_config()
    return {
        "name": "Corporate Gateway Service",
        "tier": 9,
        "entry_point": "POST /corporate/process",
        "version": app_settings.app.version,
        "environment": env_config.mode.value,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "ok",
        "service": "corporate_gateway",
        "tier": 9,
    }


# --- Main ---
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def main():
    """Run the Corporate Gateway service."""
    import uvicorn
    from shared.service_registry import ServiceName, ServiceRegistry

    app_settings = get_settings()

    uvicorn.run(
        "services.corporate_gateway.main:app",
        host=app_settings.api.host,
        port=ServiceRegistry.get_port(ServiceName.CORPORATE_GATEWAY),
        reload=app_settings.is_development,
        workers=(
            app_settings.api.workers_dev
            if app_settings.is_development
            else app_settings.api.workers_prod
        ),
    )


if __name__ == "__main__":
    main()
