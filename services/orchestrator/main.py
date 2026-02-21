"""
Orchestrator Main Service.

FastAPI entrypoint for the research orchestrator.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from shared.config import get_settings
from shared.logging import get_logger, setup_logging, LogConfig, RequestLoggingMiddleware
from shared.service_registry import ServiceName, ServiceRegistry
from shared.vocab import load_vocab

# Initialize structured logging globally
setup_logging(LogConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    service_name="orchestrator",
))

logger = get_logger(__name__)

# Global state
research_graph = None

orchestrator_vocab = load_vocab("orchestrator")
vocab_settings = orchestrator_vocab.get("settings", {})

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI app."""
    logger.info("Starting Orchestrator service")
    logger.info("Service is in REDESIGN mode - Kernel logic removed.")

    yield
    logger.info("Orchestrator service stopped")


# Create FastAPI app
app = FastAPI(
    title="Project Orchestrator",
    description="Research orchestration service (Redesign in progress)",
    version="0.5.0",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(RequestLoggingMiddleware)


# ============================================================================
# Request/Response Models
# ============================================================================


class ResearchRequest(BaseModel):
    """Research job request."""
    query: str = Field(..., min_length=1, description="Research query")
    depth: int = Field(default=2, ge=1, le=5, description="Research depth")
    max_sources: int = Field(default=10, ge=1, le=50, description="Max sources")


class ResearchResponse(BaseModel):
    """Research job response."""
    job_id: str
    status: str
    report: str | None = None
    confidence: float = 0.0
    sources_count: int = 0
    facts_count: int = 0


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
        async with httpx.AsyncClient(timeout=vocab_settings.get("mcp_tool_list_timeout", 10.0)) as client:
            resp = await client.get(f"{mcp_url}/tools")
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.warning(f"Could not reach MCP Host for tool list: {e}")
    return {"tools": []}


@app.post("/research", response_model=ResearchResponse)
async def start_research(request: ResearchRequest):
    """
    Start research job (Redesign in progress).
    """
    raise HTTPException(
        status_code=501, 
        detail="Research engine is currently under redesign. Kernel and Workers have been removed."
    )


@app.post("/tools/{tool_name}")
async def call_tool(tool_name: str, arguments: dict[str, Any]):
    """Call a specific MCP tool via MCP Host service."""
    try:
        mcp_url = ServiceRegistry.get_url(ServiceName.MCP_HOST)
        async with httpx.AsyncClient(timeout=30.0) as client:
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


@app.get("/research/stream")
async def stream_research(query: str, depth: int = 2, max_sources: int = 10):
    """
    Stream research results (Redesign in progress).
    """
    async def event_generator():
        yield f"data: {json.dumps({'event': 'error', 'message': 'Research engine is under redesign.'})}\n\n"

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
    settings = get_settings()
    uvicorn.run(
        "services.orchestrator.main:app",
        host=settings.api_host,
        port=ServiceRegistry.get_port(ServiceName.ORCHESTRATOR),
        reload=False,
        loop="asyncio",
    )


if __name__ == "__main__":
    main()
