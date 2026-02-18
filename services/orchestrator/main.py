"""
Orchestrator Main Service.

FastAPI entrypoint for the research orchestrator.

v4.1: Dual-mode â€” kernel-first with legacy graph fallback.
The USE_KERNEL_PIPELINE env var / config controls which engine runs.
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

from kernel.flow.graph import GraphState, compile_research_graph
from shared.config import get_settings
from shared.logging import get_logger
from shared.logging.middleware import RequestLoggingMiddleware
from shared.prompts import get_agent_prompt, get_kernel_config
from shared.schemas import ResearchStatus
from shared.service_registry import ServiceName, ServiceRegistry

logger = get_logger(__name__)

# Global state
research_graph = None

from shared.vocab import load_vocab
orchestrator_vocab = load_vocab("orchestrator")
vocab_settings = orchestrator_vocab.get("settings", {})

# Feature flag: kernel vs legacy graph
USE_KERNEL_ENV = os.getenv("USE_KERNEL_PIPELINE", "").lower()
if USE_KERNEL_ENV in ("true", "1", "yes"):
    USE_KERNEL = True
elif USE_KERNEL_ENV in ("false", "0", "no"):
    USE_KERNEL = False
else:
    USE_KERNEL = vocab_settings.get("use_kernel_default", True)


def _kernel_level_from_complexity(query: str, depth: int) -> str:
    """Determine starting kernel level from query complexity.

    Mapping is loaded from ``kernel.yaml`` ``kernel_cell.complexity_level_mapping``
    and depth escalation from ``kernel_cell.depth_escalation``.
    """
    try:
        from kernel.logic.complexity import classify_complexity

        score = classify_complexity(query)
        tier = score.tier.value

        v_esc = orchestrator_vocab.get("escalation", {})

        # Load tierâ†’level mapping from config
        mapping = get_kernel_config("kernel_cell.complexity_level_mapping") or {}
        level = mapping.get(tier, v_esc.get("default_level", "manager"))

        # Depth escalation from config
        escalation = get_kernel_config("kernel_cell.depth_escalation") or {}
        esc_threshold = escalation.get("threshold", v_esc.get("threshold", 4))
        esc_min_level = escalation.get("min_level", v_esc.get("min_level", "director"))
        esc_from = escalation.get("escalate_from", v_esc.get("escalate_from", ["staff", "senior_staff", "manager"]))

        if depth >= esc_threshold and level in esc_from:
            level = esc_min_level

        return level
    except Exception:
        return orchestrator_vocab.get("escalation", {}).get("default_level", "manager")


def _domain_from_query(query: str) -> str:
    """Detect primary domain from query text using vocab-backed classification.

    Delegates to ``PromptFactory.detect_domain()`` which loads keywords from
    ``configs/vocab/classification.yaml``.
    """
    try:
        from kernel.core.prompt_factory import PromptFactory

        factory = PromptFactory()
        return factory.detect_domain(query).value
    except Exception:
        return "research"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI app."""
    global research_graph

    logger.info("Starting Orchestrator service")
    logger.info(f"Kernel mode: {'KERNEL' if USE_KERNEL else 'LEGACY GRAPH'}")

    # =========================================================================
    # Initialize Orchestrator-owned subsystems only.
    # Other services (MCP Host, Vault, SwarmManager) are accessed via REST API.
    # =========================================================================
    try:
        # Organization structure (owned by Orchestrator, loaded from kernel.yaml)
        from kernel.core.organization import (
            get_organization,
            initialize_from_config,
        )

        org = get_organization()
        if not org.list_departments():
            initialize_from_config(org)
            dept_names = [d.name for d in org.list_departments()]
            logger.info(f"Organization initialized from config: {dept_names}")

        # Conversation memory (owned by Orchestrator)
        from kernel.memory.conversation import get_conversation_manager

        get_conversation_manager()
        logger.info("Conversation Memory initialized")

        # =====================================================================
        # KERNEL DEPENDENCY INJECTION
        # =====================================================================
        # Register Tool Registry (Remote MCP Host)
        try:
            from kernel.actions.remote_tool_registry import RemoteToolRegistry
            from kernel.interfaces.tool_registry import register_tool_registry

            # Use Remote Registry to talk to MCP Host Service
            registry = RemoteToolRegistry()
            register_tool_registry(registry)
            logger.info("Dependency Injection: Registered RemoteToolRegistry (MCP Client)")
        except Exception as e:
            logger.warning(f"Dependency Injection Failed (ToolRegistry): {e}")

        # Register Fact Store (RAG Service)
        try:
            from services.rag_service.core.fact_store import FactStore
            from kernel.interfaces.fact_store import register_fact_store

            # Note: FactStore needs to be instantiated or singleton retrieved
            # The original code instantiated it: store = FactStore()
            # We should probably use a singleton if acceptable, or instantiate here.
            # Given it uses VectorStore which might be expensive, singleton is better.
            # But FactStore class doesn't seem to have a singleton getter.
            # We will instantiate it here for the kernel.
            
            fact_store_instance = FactStore()
            register_fact_store(fact_store_instance)
            logger.info("Dependency Injection: Registered FactStore instance")
        except Exception as e:
            logger.warning(f"Dependency Injection Failed (FactStore): {e}")

    except Exception as e:
        logger.error(f"Failed to initialize orchestrator subsystems: {e}")

    # Compile research graph (always available as fallback)
    research_graph = compile_research_graph()
    logger.info("Research graph compiled")

    # Verify MCP Host connectivity (non-blocking)
    if USE_KERNEL:
        try:
            from kernel.actions.tool_bridge import verify_mcp_connectivity

            connected = await verify_mcp_connectivity()
            if connected:
                logger.info("MCP Host connectivity verified for kernel mode")
            else:
                logger.warning("MCP Host not reachable â€” kernel will retry on first request")
        except Exception as e:
            logger.warning(f"MCP Host connectivity check failed: {e}")

    yield

    logger.info("Orchestrator service stopped")


# Create FastAPI app
app = FastAPI(
    title="Kea Orchestrator",
    description="Research orchestration service with MCP tool integration",
    version="4.1.0",
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
    seed_facts: list[dict] | None = Field(
        default=None, description="Facts from previous attempt to build upon"
    )
    error_feedback: list[dict] | None = Field(
        default=None, description="Errors from previous attempt to avoid"
    )


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
    # Proxy active session count from MCP Host via its REST API
    active_sessions = 0
    try:
        mcp_url = ServiceRegistry.get_url(ServiceName.MCP_HOST)
        async with httpx.AsyncClient(timeout=vocab_settings.get("health_check_timeout", 2.0)) as client:
            resp = await client.get(f"{mcp_url}/health")
            if resp.status_code == 200:
                active_sessions = resp.json().get("active_sessions", 0)
    except Exception:
        pass  # MCP Host may not be up yet; non-fatal

    return {
        "status": "healthy",
        "service": "orchestrator",
        "active_sessions": active_sessions,
        "kernel_mode": USE_KERNEL,
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
    Start a synchronous research job.

    Uses the kernel pipeline (KernelCell with cognitive cycle, corporate
    hierarchy, working memory) by default. Falls back to legacy LangGraph
    pipeline when USE_KERNEL_PIPELINE=false.
    """
    global research_graph

    job_id = f"job-{uuid.uuid4().hex[:8]}"

    seed_count = len(request.seed_facts) if request.seed_facts else 0
    error_count = len(request.error_feedback) if request.error_feedback else 0
    logger.info(
        f"Starting research job {job_id} (seed_facts={seed_count}, errors={error_count})",
        extra={"query": request.query[:100]},
    )

    # â”€â”€ Kernel Pipeline â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if USE_KERNEL:
        try:
            from kernel.core.kernel_cell import run_kernel
            from kernel.io.response_formatter import (
                envelope_to_research_response,
            )
            from kernel.actions.tool_bridge import create_tool_executor

            # Determine starting level and domain
            level = _kernel_level_from_complexity(request.query, request.depth)
            domain = _domain_from_query(request.query)

            # Budget scales with depth
            v_budget = vocab_settings.get("base_budget", 30000)
            base_budget = int(get_kernel_config("kernel_cell.budget.default_max_tokens") or v_budget)
            budget = base_budget * max(1, request.depth)

            logger.info(
                f"Kernel mode: level={level}, domain={domain}, budget={budget}, "
                f"depth={request.depth}"
            )

            tool_executor = create_tool_executor(query=request.query)

            envelope = await run_kernel(
                query=request.query,
                tool_executor=tool_executor,
                level=level,
                domain=domain,
                budget=budget,
                max_depth=request.depth + 1,
                seed_facts=request.seed_facts,
                error_feedback=request.error_feedback,
            )

            result = envelope_to_research_response(envelope)

            return ResearchResponse(
                job_id=job_id,
                status="completed",
                report=result.get("report"),
                confidence=result.get("confidence", 0.0),
                sources_count=result.get("sources_count", 0),
                facts_count=result.get("facts_count", 0),
                facts=result.get("facts", []),
                errors=result.get("errors", []),
            )

        except Exception as e:
            logger.error(f"Kernel pipeline failed: {e}", exc_info=True)
            if not research_graph:
                raise HTTPException(status_code=500, detail=str(e))
            logger.info("Falling back to legacy graph pipeline")

    # â”€â”€ Legacy Graph Pipeline (fallback) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if not research_graph:
        raise HTTPException(status_code=503, detail="Research graph not initialized")

    initial_state: GraphState = {
        "job_id": job_id,
        "query": request.query,
        "path": "",
        "status": ResearchStatus.PENDING.value,
        "sub_queries": [],
        "hypotheses": [],
        "facts": request.seed_facts or [],
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
        "error_feedback": request.error_feedback or [],
    }

    try:
        final_state = await research_graph.ainvoke(initial_state)

        return ResearchResponse(
            job_id=job_id,
            status=final_state.get("status", "completed"),
            report=final_state.get("report"),
            confidence=final_state.get("confidence", 0.0),
            sources_count=len(final_state.get("sources", [])),
            facts_count=len(final_state.get("facts", [])),
            facts=final_state.get("facts", []),
            errors=final_state.get("error_feedback", []),
        )

    except Exception as e:
        error_msg = str(e) or f"Unknown error ({type(e).__name__})"
        logger.error(f"Research job {job_id} failed: {error_msg}", exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)


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

    Uses kernel pipeline when enabled, falls back to legacy pipeline.
    """
    from kernel.flow.pipeline import get_research_pipeline

    try:
        pipeline = await get_research_pipeline()

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


@app.get("/research/stream")
async def stream_research(query: str, depth: int = 2, max_sources: int = 10):
    """
    Stream research results via Server-Sent Events (SSE).

    Uses kernel pipeline when enabled, falls back to legacy streaming.
    """

    async def event_generator():
        global research_graph
        job_id = f"stream-{uuid.uuid4().hex[:8]}"

        yield f"data: {json.dumps({'event': 'start', 'job_id': job_id, 'query': query})}\n\n"

        # â”€â”€ Kernel Streaming â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if USE_KERNEL:
            try:
                from kernel.core.kernel_cell import run_kernel
                from kernel.io.response_formatter import (
                    envelope_to_sse_events,
                )
                from kernel.actions.tool_bridge import create_tool_executor

                v_streaming = orchestrator_vocab.get("streaming", {}).get("phases", {})
                yield f"data: {json.dumps({'event': 'phase', 'phase': v_streaming.get('kernel', 'kernel_processing')})}\n\n"

                level = _kernel_level_from_complexity(query, depth)
                domain = _domain_from_query(query)
                base_budget = int(
                    get_kernel_config("kernel_cell.budget.default_max_tokens") or vocab_settings.get("base_budget", 30000)
                )
                budget = base_budget * max(1, depth)

                tool_executor = create_tool_executor(query=query)

                envelope = await run_kernel(
                    query=query,
                    tool_executor=tool_executor,
                    level=level,
                    domain=domain,
                    budget=budget,
                    max_depth=depth + 1,
                )

                async for event in envelope_to_sse_events(envelope, job_id):
                    yield f"data: {json.dumps(event)}\n\n"

                return
            except Exception as e:
                logger.error(f"Kernel streaming failed: {e}", exc_info=True)
                yield f"data: {json.dumps({'event': 'phase', 'phase': orchestrator_vocab.get('streaming', {}).get('phases', {}).get('fallback', 'fallback_to_legacy')})}\n\n"

        # â”€â”€ Legacy Graph Streaming (fallback) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if not research_graph:
            yield f"data: {json.dumps({'event': 'error', 'message': 'Research graph not initialized'})}\n\n"
            return

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
            import os

            if os.getenv("OPENROUTER_API_KEY"):
                from shared.llm import LLMConfig, OpenRouterProvider
                from shared.llm.provider import LLMMessage, LLMRole

                provider = OpenRouterProvider()
                config = LLMConfig(temperature=0.7, max_tokens=32768)

                v_streaming = orchestrator_vocab.get("streaming", {}).get("phases", {})
                yield f"data: {json.dumps({'event': 'phase', 'phase': v_streaming.get('planning', 'planning')})}\n\n"

                planner_prompt = (
                    get_agent_prompt("planner") or "You are a research planner. Be concise."
                )
                messages = [
                    LLMMessage(role=LLMRole.SYSTEM, content=planner_prompt),
                    LLMMessage(role=LLMRole.USER, content=f"Plan research for: {query}"),
                ]

                async for chunk in provider.stream(messages, config):
                    if chunk.content:
                        yield f"data: {json.dumps({'event': 'chunk', 'phase': 'planning', 'content': chunk.content})}\n\n"

                yield f"data: {json.dumps({'event': 'phase', 'phase': v_streaming.get('research', 'research')})}\n\n"
                final_state = await research_graph.ainvoke(initial_state)

                yield f"data: {json.dumps({'event': 'phase', 'phase': v_streaming.get('synthesis', 'synthesis')})}\n\n"

                facts_text = "\n".join([str(f)[:100] for f in final_state.get("facts", [])[:5]])

                synth_prompt = (
                    get_agent_prompt("synthesizer")
                    or "You are a research synthesizer. Create concise reports."
                )
                messages = [
                    LLMMessage(role=LLMRole.SYSTEM, content=synth_prompt),
                    LLMMessage(
                        role=LLMRole.USER,
                        content=f"Synthesize research on: {query}\n\nFacts:\n{facts_text}",
                    ),
                ]

                report_chunks = []
                async for chunk in provider.stream(messages, config):
                    if chunk.content:
                        report_chunks.append(chunk.content)
                        yield f"data: {json.dumps({'event': 'chunk', 'phase': 'synthesis', 'content': chunk.content})}\n\n"

                final_report = "".join(report_chunks) or final_state.get("report", "")

            else:
                final_state = await research_graph.ainvoke(initial_state)
                final_report = final_state.get("report", "Research completed without LLM.")

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
