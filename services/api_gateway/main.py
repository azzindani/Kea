"""
API Gateway Main Service.

FastAPI entrypoint for the public API.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from shared.config import get_settings
from shared.logging import setup_logging, get_logger, LogConfig
from shared.logging.middleware import RequestLoggingMiddleware
from shared.logging.metrics import set_system_info

from services.api_gateway.routes import jobs, memory, mcp, system


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    settings = get_settings()
    
    # Setup logging
    setup_logging(LogConfig(
        level=settings.log_level,
        format=settings.log_format,
        service_name="api_gateway",
    ))
    
    # Set system info metrics
    set_system_info(version="0.1.0", environment=settings.environment.value)
    
    logger.info("Starting API Gateway")
    
    yield
    
    logger.info("API Gateway stopped")


# Create FastAPI app
app = FastAPI(
    title="Kea Research Engine API",
    description="API Gateway for the Kea Distributed Autonomous Research Engine",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(memory.router, prefix="/api/v1/memory", tags=["Memory"])
app.include_router(mcp.router, prefix="/api/v1/mcp", tags=["MCP"])
app.include_router(system.router, prefix="/api/v1/system", tags=["System"])


# ============================================================================
# Root Routes
# ============================================================================

@app.get("/")
async def root():
    """API root."""
    return {
        "name": "Kea Research Engine",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "api_gateway",
    }


# ============================================================================
# Main
# ============================================================================

def main():
    """Run the API gateway."""
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "services.api_gateway.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
    )


if __name__ == "__main__":
    main()
