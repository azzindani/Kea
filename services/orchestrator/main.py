"""
Orchestrator Main Service.

FastAPI entrypoint for the kernel orchestrator.
"""

from __future__ import annotations

import asyncio
import json
import sys
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from prometheus_client import make_asgi_app

from shared.config import get_settings
from shared.logging import get_logger, setup_logging, LogConfig, RequestLoggingMiddleware
from shared.service_registry import ServiceName, ServiceRegistry
from shared.vocab import load_vocab

# Load settings
settings = get_settings()

# Initialize structured logging globally
setup_logging(LogConfig(
    level=settings.logging.level,
    service_name="orchestrator",
))

logger = get_logger(__name__)

# Global state
workflow_graph = None

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifecycle manager for the FastAPI app."""
    logger.info("Starting Orchestrator service")
    logger.info("Service is in REDESIGN mode - Kernel logic removed.")

    yield
    logger.info("Orchestrator service stopped")


# (Settings already loaded above)

# Create FastAPI app
app = FastAPI(
    title=settings.app.name,
    description="Kernel orchestration service (Redesign in progress)",
    version=settings.app.version,
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(RequestLoggingMiddleware)
app.mount("/metrics", make_asgi_app())


# ============================================================================
# Request/Response Models
# ============================================================================


class ExecutionRequest(BaseModel):
    """General execution request."""
    query: str = Field(..., min_length=1, description="Task query")
    depth: int = Field(
        default=settings.kernel.default_depth, 
        ge=1, 
        le=settings.kernel.max_depth, 
        description="Execution depth"
    )
    max_steps: int = Field(
        default=settings.kernel.default_max_steps, 
        ge=1, 
        le=settings.kernel.max_steps, 
        description="Max steps"
    )


class ExecutionResponse(BaseModel):
    """General execution response."""
    job_id: str
    status: str
    output: str | None = None
    confidence: float = 0.0
    steps_count: int = 0


# ============================================================================
# Routes
# ============================================================================


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "orchestrator",
        "mode": "redesign",
    }


@app.get("/tools")
async def list_tools():
    """List all available MCP tools via MCP Host service."""
    try:
        mcp_url = ServiceRegistry.get_url(ServiceName.MCP_HOST)
        async with httpx.AsyncClient(timeout=settings.mcp.discovery_timeout) as client:
            resp = await client.get(f"{mcp_url}/tools")
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.warning(f"Could not reach MCP Host for tool list: {e}")
    return {"tools": []}


@app.post("/execute", response_model=ExecutionResponse)
async def start_execution(request: ExecutionRequest):
    """
    Start execution job (Redesign in progress).
    """
    raise HTTPException(
        status_code=501, 
        detail="Kernel engine is currently under redesign."
    )


@app.post("/tools/{tool_name}")
async def call_tool(tool_name: str, arguments: dict[str, Any]):
    """Call a specific MCP tool via MCP Host service."""
    try:
        mcp_url = ServiceRegistry.get_url(ServiceName.MCP_HOST)
        async with httpx.AsyncClient(timeout=settings.timeouts.default) as client:
            resp = await client.post(
                f"{mcp_url}/tools/execute",
                json={"tool_name": tool_name, "arguments": arguments},
            )
            if resp.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            return resp.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/execute/stream")
async def stream_execution(
    query: str, 
    depth: int | None = None, 
    max_steps: int | None = None
):
    """
    Stream execution results (Redesign in progress).
    """
    global settings
    depth = depth or settings.kernel.default_depth
    max_steps = max_steps or settings.kernel.default_max_steps
    async def event_generator():
        yield f"data: {json.dumps({'event': 'error', 'message': 'Kernel engine is under redesign.'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# ============================================================================
# Main
# ============================================================================

# Force Proactor loop for Windows subprocess support
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def main():
    """Run the orchestrator service."""
    import uvicorn
    global settings
    uvicorn.run(
        "services.orchestrator.main:app",
        host=settings.api.host,
        port=ServiceRegistry.get_port(ServiceName.ORCHESTRATOR),
        reload=False,
        loop="asyncio",
    )


if __name__ == "__main__":
    main()
