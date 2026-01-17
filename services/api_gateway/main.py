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
from shared.logging import setup_logging, get_logger, LogConfig
from shared.logging.middleware import RequestLoggingMiddleware
from shared.logging.metrics import set_system_info
from shared.environment import get_environment_config

from services.api_gateway.routes import (
    jobs, memory, mcp, system, artifacts, interventions, llm, graph,
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
    env_config = get_environment_config()
    
    if env_config.is_production:
        required = ["DATABASE_URL", "JWT_SECRET"]
        missing = [k for k in required if not os.getenv(k)]
        
        if missing:
            raise RuntimeError(f"Missing required env vars for production: {missing}")
        
        jwt_secret = os.getenv("JWT_SECRET", "")
        if len(jwt_secret) < 32:
            raise RuntimeError("JWT_SECRET must be at least 32 characters")
    
    logger.info(f"Configuration validated for {env_config.mode.value}")


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    set_system_info(version="0.3.0", environment=env_config.mode.value)
    
    # Initialize database
    from shared.database import get_database_pool
    await get_database_pool()
    
    # Initialize user management
    from shared.users.manager import get_user_manager, get_api_key_manager
    from shared.conversations import get_conversation_manager
    
    await get_user_manager()
    await get_api_key_manager()
    await get_conversation_manager()
    
    logger.info(f"API Gateway v0.3.0 started [{env_config.mode.value}]")
    
    yield
    
    # Cleanup
    from shared.database import close_database_pool
    await close_database_pool()
    
    logger.info("API Gateway stopped")


# Create FastAPI app
app = FastAPI(
    title="Kea Research Engine API",
    description="API Gateway for the Kea Distributed Autonomous Research Engine",
    version="0.3.0",
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
app.include_router(graph.router, prefix="/api/v1/graph", tags=["Graph"])


# ============================================================================
# Root Routes
# ============================================================================

@app.get("/")
async def root():
    """API root."""
    env_config = get_environment_config()
    return {
        "name": "Kea Research Engine",
        "version": "0.3.0",
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
    
    Checks: database, redis, qdrant, memory.
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
    env_config = get_environment_config()
    
    uvicorn.run(
        "services.api_gateway.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=env_config.is_development,
        workers=1 if env_config.is_development else 4,
    )


if __name__ == "__main__":
    main()

