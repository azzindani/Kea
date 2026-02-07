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
from services.mcp_host.core.session_registry import get_session_registry
from shared.config import get_settings
from shared.logging import get_logger
from shared.logging.middleware import RequestLoggingMiddleware
from shared.schemas import ResearchStatus

logger = get_logger(__name__)

# Global state
registry = None
research_graph = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI app."""
    global registry, research_graph
    
    settings = get_settings()
    
    logger.info("Starting Orchestrator service")
    
    # Initialize Registry (Auto-Discovery)
    registry = get_session_registry()
    
    # Static RAG Population (Background)
    # This pushes the ~660 discovered tools (name+docstring) to Postgres
    # so the Planner can find them via semantic search.
    import asyncio
    asyncio.create_task(registry.register_discovered_tools())
    
    # await registry.list_all_tools() # DISABLED: Warmup causes hangs in threaded startup. Rely on JIT.
    logger.info(f"Registry initialized (Lazy Mode + Static RAG)")

    # =========================================================================
    # Initialize Enterprise Subsystems
    # =========================================================================
    try:
        from services.vault.core.audit_trail import configure_audit_trail, AuditBackend
        from services.swarm_manager.core.compliance import get_compliance_engine
        
        # 2. Compliance Engine (Guardrails)
        compliance = get_compliance_engine()
        logger.info(f"Compliance Engine initialized with {len(compliance.rules)} rule sets")
        
        # 3. Organization (The Corporate Structure)
        from services.orchestrator.core.organization import get_organization, Domain
        org = get_organization()
        if not org.list_departments():
            org.create_department("Research", Domain.RESEARCH)
            org.create_department("Finance", Domain.FINANCE)
            org.create_department("Legal", Domain.LEGAL)
            logger.info("Organization structure initialized: Research, Finance, Legal")

        # 4. Memory (The Mind)
        from services.orchestrator.core.conversation import get_conversation_manager
        memory = get_conversation_manager()
        logger.info("Conversation Memory initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize enterprise systems: {e}")
    
    # Compile research graph
    research_graph = compile_research_graph()
    logger.info("Research graph compiled")
    
    yield
    
    # Cleanup
    if registry:
        await registry.shutdown()
    
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
    
    # Cross-attempt context sharing (for retry scenarios)
    seed_facts: list[dict] | None = Field(default=None, description="Facts from previous attempt to build upon")
    error_feedback: list[dict] | None = Field(default=None, description="Errors from previous attempt to avoid")


class ResearchResponse(BaseModel):
    """Research job response."""
    job_id: str
    status: str
    report: str | None = None
    confidence: float = 0.0
    sources_count: int = 0
    facts_count: int = 0
    
    # Cross-attempt context (for retry scenarios)
    facts: list[dict] = []  # Actual facts for passing to next attempt
    errors: list[dict] = []  # Errors encountered for next attempt to avoid


# ============================================================================
# Routes
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "orchestrator",
        "active_sessions": len(registry.active_sessions) if registry else 0,
    }


@app.get("/tools")
async def list_tools():
    """List all available MCP tools."""
    if not registry:
        return {"tools": []}
    
    tools = await registry.list_all_tools()
    return {"tools": tools}


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
    
    seed_count = len(request.seed_facts) if request.seed_facts else 0
    error_count = len(request.error_feedback) if request.error_feedback else 0
    logger.info(f"Starting research job {job_id} (seed_facts={seed_count}, errors={error_count})", 
                extra={"query": request.query[:100]})
    
    # Build initial state with seed context (for cross-attempt sharing)
    initial_state: GraphState = {
        "job_id": job_id,
        "query": request.query,
        "path": "",
        "status": ResearchStatus.PENDING.value,
        "sub_queries": [],
        "hypotheses": [],
        "facts": request.seed_facts or [],  # Initialize with seed facts
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
        "error_feedback": request.error_feedback or [],  # Initialize with previous errors
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
            facts=final_state.get("facts", []),  # Return facts for cross-attempt sharing
            errors=final_state.get("error_feedback", []),  # Return errors for next attempt
        )
        
    except Exception as e:
        error_msg = str(e) or f"Unknown error ({type(e).__name__})"
        logger.error(f"Research job {job_id} failed: {error_msg}", exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)


@app.post("/tools/{tool_name}")
async def call_tool(tool_name: str, arguments: dict[str, Any]):
    """Call a specific MCP tool directly."""
    if not registry:
        raise HTTPException(status_code=503, detail="Registry not initialized")
    
    server_name = registry.get_server_for_tool(tool_name)
    if not server_name:
        # JIT
        await registry.list_all_tools()
        server_name = registry.get_server_for_tool(tool_name)
        
    if not server_name:
         raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")

    try:
        session = await registry.get_session(server_name)
        result = await session.call_tool(tool_name, arguments)
        
        return {
            "tool": tool_name,
            "is_error": result.isError,
            "content": [c.model_dump() for c in result.content],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Pipeline Endpoint (Chat)
# ============================================================================

class ChatMessageRequest(BaseModel):
    conversation_id: str
    content: str
    user_id: str
    attachments: list[str] = []

@app.post("/chat/message")
async def process_chat_message(request: ChatMessageRequest):
    """
    Process a chat message through the research pipeline.
    
    This endpoint:
    1. Classifies the query
    2. Checks cache
    3. Runs research graph if needed
    4. Logs to audit trail
    5. Returns the result (content, sources, etc.)
    """
    from services.orchestrator.core.pipeline import get_research_pipeline
    
    try:
        pipeline = await get_research_pipeline()
        
        # Note: pipeline.process_message does NOT store to DB if called directly.
        # But pipeline.process_and_store DOES.
        # However, Gateway's conversation route typically adds the User message first,
        # then expects the Assistant message to be generated.
        # If we use process_message, we just get the result, and Gateway can save the Assistant message.
        # OR we let Orchestrator save it.
        # Let's check conversations.py again.
        # conversations.py: adds User msg, then calls pipeline.process_message, then adds Assistant msg.
        # So we should return the Result, and let Gateway save the Assistant msg (or Orchestrator).
        # To keep Gateway as the "Interface Layer", it handles DB interaction for the conversation view.
        # Orchestrator provides the "Result".
        
        result = await pipeline.process_message(
            conversation_id=request.conversation_id,
            content=request.content,
            user_id=request.user_id,
            attachments=request.attachments,
        )
        
        return {
            "content": result.content,
            "confidence": result.confidence,
            "sources": result.sources,
            "tool_calls": result.tool_calls,
            "facts": result.facts,
            "duration_ms": result.duration_ms,
            "query_type": result.query_type,
            "was_cached": result.was_cached,
        }
        
    except Exception as e:
        logger.error(f"Pipeline processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



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
                config = LLMConfig(temperature=0.7, max_tokens=32768)
                
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

# Force Proactor loop for Windows subprocess support
import sys
import asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

def main():
    """Run the orchestrator service."""
    import uvicorn
    
    settings = get_settings()
    
    from shared.service_registry import ServiceRegistry, ServiceName
    
    uvicorn.run(
        "services.orchestrator.main:app",
        host=settings.api_host,
        port=ServiceRegistry.get_port(ServiceName.ORCHESTRATOR),
        reload=False, 
        loop="asyncio",
    )


if __name__ == "__main__":
    main()
