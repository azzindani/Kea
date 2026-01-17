"""
Orchestrator Main Service.

FastAPI entrypoint for the research orchestrator.
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from services.orchestrator.core.graph import compile_research_graph, GraphState
from services.orchestrator.mcp.client import get_mcp_orchestrator
from services.orchestrator.config import get_settings
from shared.logging import get_logger
from shared.middleware import RequestLoggingMiddleware
from shared.schemas import ResearchStatus

logger = get_logger(__name__)

# Global state
mcp_orchestrator = None
research_graph = None
server_configs = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI app."""
    global mcp_orchestrator, research_graph, server_configs
    
    settings = get_settings()
    
    logger.info("Starting Orchestrator service")
    
    # Initialize MCP orchestrator
    mcp_orchestrator = get_mcp_orchestrator()
    
    # Start MCP servers based on config
    server_configs = [
        {"name": server.name, "command": server.command}
        for server in settings.mcp.servers
        if server.enabled and server.command
    ]
    
    if server_configs:
        await mcp_orchestrator.start_servers(server_configs)
        logger.info(f"Started {len(server_configs)} MCP servers")
    
    # Compile research graph
    research_graph = compile_research_graph()
    logger.info("Research graph compiled")
    
    yield
    
    # Cleanup
    if mcp_orchestrator:
        await mcp_orchestrator.stop_servers()
    
    logger.info("Orchestrator service stopped")


# Create FastAPI app
app = FastAPI(
    title="Kea Orchestrator",
    description="Research orchestration service with MCP tool integration",
    version="0.1.0",
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
        "mcp_servers": len(mcp_orchestrator._servers) if mcp_orchestrator else 0,
    }


@app.get("/tools")
async def list_tools():
    """List all available MCP tools."""
    if not mcp_orchestrator:
        return {"tools": []}
    
    return {
        "tools": [
            {"name": t.name, "description": t.description}
            for t in mcp_orchestrator.tools
        ]
    }


@app.post("/research", response_model=ResearchResponse)
async def start_research(request: ResearchRequest):
    """
    Start a synchronous research job.
    
    For async jobs, use POST /jobs instead.
    """
    global research_graph
    
    if not research_graph:
        raise HTTPException(status_code=503, detail="Research graph not initialized")
    
    job_id = f"job-{uuid.uuid4().hex[:8]}"
    
    logger.info(f"Starting research job {job_id}", extra={"query": request.query[:100]})
    
    # Build initial state
    initial_state: GraphState = {
        "job_id": job_id,
        "query": request.query,
        "path": "",
        "status": ResearchStatus.PENDING.value,
        "sub_queries": [],
        "hypotheses": [],
        "facts": [],
        "sources": [],
        "artifacts": [],
        "generator_output": "",
        "critic_feedback": "",
        "judge_verdict": "",
        "report": "",
        "confidence": 0.0,
        "iteration": 0,
        "max_iterations": request.depth,
        "should_continue": True,
        "error": None,
    }
    
    try:
        # Execute the research graph
        final_state = await research_graph.ainvoke(initial_state)
        
        return ResearchResponse(
            job_id=job_id,
            status=final_state.get("status", "completed"),
            report=final_state.get("report"),
            confidence=final_state.get("confidence", 0.0),
            sources_count=len(final_state.get("sources", [])),
            facts_count=len(final_state.get("facts", [])),
        )
        
    except Exception as e:
        logger.error(f"Research job {job_id} failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/{tool_name}")
async def call_tool(tool_name: str, arguments: dict[str, Any]):
    """Call a specific MCP tool directly."""
    if not mcp_orchestrator:
        raise HTTPException(status_code=503, detail="MCP orchestrator not initialized")
    
    result = await mcp_orchestrator.call_tool(tool_name, arguments)
    
    return {
        "tool": tool_name,
        "is_error": result.isError,
        "content": [c.model_dump() for c in result.content],
    }


# ============================================================================
# Streaming Endpoints (SSE)
# ============================================================================

from fastapi.responses import StreamingResponse
import json


@app.get("/research/stream")
async def stream_research(query: str, depth: int = 2, max_sources: int = 10):
    """
    Stream research results via Server-Sent Events (SSE).
    
    This endpoint provides real-time updates as the research progresses:
    - Planning phase updates
    - Tool call results
    - LLM streaming output
    - Final report
    
    Example:
        curl -N "http://localhost:8000/research/stream?query=What%20is%20AI"
    """
    
    async def event_generator():
        global research_graph
        
        if not research_graph:
            yield f"data: {json.dumps({'event': 'error', 'message': 'Research graph not initialized'})}\n\n"
            return
        
        job_id = f"stream-{uuid.uuid4().hex[:8]}"
        
        # Send start event
        yield f"data: {json.dumps({'event': 'start', 'job_id': job_id, 'query': query})}\n\n"
        
        # Build initial state
        initial_state: GraphState = {
            "job_id": job_id,
            "query": query,
            "path": "",
            "status": ResearchStatus.PENDING.value,
            "sub_queries": [],
            "hypotheses": [],
            "facts": [],
            "sources": [],
            "artifacts": [],
            "generator_output": "",
            "critic_feedback": "",
            "judge_verdict": "",
            "report": "",
            "confidence": 0.0,
            "iteration": 0,
            "max_iterations": depth,
            "should_continue": True,
            "error": None,
        }
        
        try:
            # Stream LLM if available
            import os
            if os.getenv("OPENROUTER_API_KEY"):
                from shared.llm import OpenRouterProvider, LLMConfig
                from shared.llm.provider import LLMMessage, LLMRole
                
                provider = OpenRouterProvider()
                config = LLMConfig(temperature=0.7, max_tokens=1000)
                
                # Phase 1: Planning
                yield f"data: {json.dumps({'event': 'phase', 'phase': 'planning'})}\n\n"
                
                messages = [
                    LLMMessage(role=LLMRole.SYSTEM, content="You are a research planner. Be concise."),
                    LLMMessage(role=LLMRole.USER, content=f"Plan research for: {query}")
                ]
                
                async for chunk in provider.stream(messages, config):
                    if chunk.content:
                        yield f"data: {json.dumps({'event': 'chunk', 'phase': 'planning', 'content': chunk.content})}\n\n"
                
                # Phase 2: Research (using graph)
                yield f"data: {json.dumps({'event': 'phase', 'phase': 'research'})}\n\n"
                
                final_state = await research_graph.ainvoke(initial_state)
                
                # Phase 3: Synthesis with streaming
                yield f"data: {json.dumps({'event': 'phase', 'phase': 'synthesis'})}\n\n"
                
                facts_text = "\n".join([str(f)[:100] for f in final_state.get("facts", [])[:5]])
                
                messages = [
                    LLMMessage(role=LLMRole.SYSTEM, content="You are a research synthesizer. Create concise reports."),
                    LLMMessage(role=LLMRole.USER, content=f"Synthesize research on: {query}\n\nFacts:\n{facts_text}")
                ]
                
                report_chunks = []
                async for chunk in provider.stream(messages, config):
                    if chunk.content:
                        report_chunks.append(chunk.content)
                        yield f"data: {json.dumps({'event': 'chunk', 'phase': 'synthesis', 'content': chunk.content})}\n\n"
                
                final_report = "".join(report_chunks) or final_state.get("report", "")
                
            else:
                # Fallback without streaming
                final_state = await research_graph.ainvoke(initial_state)
                final_report = final_state.get("report", "Research completed without LLM.")
            
            # Send completion
            yield f"data: {json.dumps({'event': 'complete', 'job_id': job_id, 'report': final_report, 'confidence': final_state.get('confidence', 0.5), 'facts_count': len(final_state.get('facts', [])), 'sources_count': len(final_state.get('sources', []))})}\n\n"
            
        except Exception as e:
            logger.error(f"Stream research error: {e}")
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# ============================================================================
# Main
# ============================================================================

def main():
    """Run the orchestrator service."""
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "services.orchestrator.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
    )


if __name__ == "__main__":
    main()
