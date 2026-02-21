"""
API Gateway Main Service.

FastAPI entrypoint for the public API.
Production-ready with security, rate limiting, and health checks.
"""

from __future__ import annotations

import os
import traceback
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from shared.config import get_settings
from shared.logging import setup_logging, get_logger, LogConfig, RequestLoggingMiddleware, set_system_info
from shared.environment import get_environment_config

from services.api_gateway.routes import (
    jobs, memory, mcp, system, artifacts, interventions, llm,
    auth, users, conversations,
)
from services.api_gateway.middleware.auth import create_auth_middleware
from services.api_gateway.middleware.rate_limit import RateLimitMiddleware
from services.api_gateway.middleware.security import (
    SecurityHeadersMiddleware,
    RequestValidationMiddleware,
    get_cors_origins,
)


logger = get_logger(__name__)


def validate_config():
    """Validate required configuration at startup."""
    settings = get_settings()
    
    if settings.app.environment == "production":
        # Check database
        if not settings.database.url:
            raise RuntimeError("Missing database.url in settings for production")
            
        # Check JWT Secret
        if not settings.auth.jwt_secret:
            raise RuntimeError("Missing auth.jwt_secret in settings for production")
        
        if len(settings.auth.jwt_secret) < 32:
            raise RuntimeError("JWT_SECRET must be at least 32 characters for production security")
    
    logger.info(f"Configuration validated for {settings.app.environment}")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan manager."""
    settings = get_settings()
    env_config = get_environment_config()
    
    # Validate config
    validate_config()
    
    # Setup logging
    setup_logging(LogConfig(
        level=env_config.log_level,
        format=settings.log_format,
        service_name="api_gateway",
    ))
    
    # Set system info metrics
    set_system_info(version=settings.app.version, environment=env_config.mode.value)
    
    # Initialize database
    from shared.database import get_database_pool
    await get_database_pool()
    
    # Initialize user management
    from shared.users.manager import get_user_manager, get_api_key_manager
    from shared.conversations import get_conversation_manager
    
    await get_user_manager()
    await get_api_key_manager()
    await get_conversation_manager()
    
    logger.info(f"API Gateway {settings.app.version} started [{env_config.mode.value}]")
    
    yield
    
    # Cleanup
    from shared.database import close_database_pool
    await close_database_pool()
    
    logger.info("API Gateway stopped")


# Load settings
settings = get_settings()


# Create FastAPI app
app = FastAPI(
    title=settings.app.name,
    description="API Gateway for the Project Distributed Autonomous Research Engine",
    version=settings.app.version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================================
# Middleware (order matters - last added = first executed)
# ============================================================================

# 1. CORS (innermost - runs last)
env_config = get_environment_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 2. Logging
app.add_middleware(RequestLoggingMiddleware)

# 3. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 4. Request validation
app.add_middleware(RequestValidationMiddleware)

# 5. Rate limiting (outermost - runs first)
app.add_middleware(RateLimitMiddleware)


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
    
    # Log full traceback
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Return appropriate response
    if env_config.is_development:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error": str(exc),
                "traceback": traceback.format_exc().split("\n"),
            },
        )
    else:
        # Production: don't leak details
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )


# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# ============================================================================
# Routers
# ============================================================================

# Auth & User Management
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["Conversations"])

# Core API
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(memory.router, prefix="/api/v1/memory", tags=["Memory"])
app.include_router(mcp.router, prefix="/api/v1/mcp", tags=["MCP"])
app.include_router(system.router, prefix="/api/v1/system", tags=["System"])
app.include_router(artifacts.router, prefix="/api/v1/artifacts", tags=["Artifacts"])
app.include_router(interventions.router, prefix="/api/v1/interventions", tags=["HITL"])
app.include_router(llm.router, prefix="/api/v1/llm", tags=["LLM"])


# ============================================================================
# Root Routes
# ============================================================================

@app.get("/")
async def root():
    """API root."""
    from shared.config import get_settings
    settings = get_settings()
    env_config = get_environment_config()
    return {
        "name": settings.app.name,
        "version": settings.app.version,
        "environment": env_config.mode.value,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Basic health check (fast)."""
    return {
        "status": "healthy",
        "service": "api_gateway",
    }


@app.get("/health/full")
async def full_health_check():
    """
    Comprehensive health check.
    
    Checks: database, Vault, RAG Service.
    """
    from shared.database.health import get_health_checker
    
    checker = get_health_checker()
    health = await checker.check_all()
    
    status_code = 200 if health.status == "healthy" else 503
    
    return JSONResponse(
        status_code=status_code,
        content=health.to_dict(),
    )


# ============================================================================
# Main
# ============================================================================

def main():
    """Run the API gateway."""
    import uvicorn
    
    settings = get_settings()
    
    from shared.service_registry import ServiceRegistry, ServiceName
    uvicorn.run(
        "services.api_gateway.main:app",
        host=settings.api.host,
        port=ServiceRegistry.get_port(ServiceName.GATEWAY),
        reload=settings.app.environment == "development",
        workers=settings.api.workers_dev if settings.app.environment == "development" else settings.api.workers_prod,
    )


if __name__ == "__main__":
    main()

