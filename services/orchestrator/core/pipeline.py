"""
Research Pipeline Integration.

Connects conversations to research graph with v4.0 modules.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime

from shared.conversations import Message, MessageRole, get_conversation_manager
from shared.environment import get_environment_config, is_feature_enabled
from shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ResearchResult:
    """Result from research pipeline."""

    content: str
    confidence: float = 0.0
    sources: list[dict] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    facts: list[dict] = field(default_factory=list)
    duration_ms: int = 0
    query_type: str = "research"
    was_cached: bool = False


class ConversationResearchPipeline:
    """
    Integrates conversations with research pipeline.

    Flow:
    1. Receive message from conversation
    2. Classify query (v4.0 query_classifier)
    3. Check cache (v4.0 context_cache)
    4. Run research if needed
    5. Audit log (v4.0 audit_trail)
    6. Store response with sources
    """

    def __init__(self):
        self._graph = None
        self._classifier = None
        self._cache = None
        self._audit = None

    async def initialize(self):
        """Initialize pipeline components."""
        config = get_environment_config()

        # Query classifier
        if is_feature_enabled("query_classifier"):
            try:
                from services.orchestrator.core.query_classifier import get_classifier

                self._classifier = get_classifier()
                logger.debug("Query classifier enabled")
            except ImportError:
                logger.warning("Query classifier not available")

        # Context cache
        if is_feature_enabled("context_cache"):
            try:
                from services.orchestrator.core.context_cache import get_context_cache

                self._cache = get_context_cache()
                logger.debug("Context cache enabled")
            except ImportError:
                logger.warning("Context cache not available")

        # Audit trail
        if is_feature_enabled("audit_trail"):
            try:
                from shared.service_registry import ServiceName, ServiceRegistry

                vault_url = ServiceRegistry.get_url(ServiceName.VAULT)

                class AuditApiClient:
                    def __init__(self, url):
                        self.url = url

                    async def log(
                        self,
                        event_type,
                        action,
                        actor="system",
                        resource="",
                        details=None,
                        parent_id="",
                        session_id="",
                    ):
                        try:
                            import httpx

                            # Map event_type to string if it is an enum
                            et = (
                                event_type.value
                                if hasattr(event_type, "value")
                                else str(event_type)
                            )

                            async with httpx.AsyncClient(timeout=2.0) as client:
                                # Fire and forget-ish, or wait? Pipeline awaits it.
                                await client.post(
                                    f"{self.url}/audit/logs",
                                    json={
                                        "event_type": et,
                                        "action": action,
                                        "actor": actor,
                                        "resource": resource,
                                        "details": details or {},
                                        "session_id": session_id,
                                    },
                                )
                        except Exception as e:
                            logger.warning(f"Failed to send audit log: {e}")

                self._audit = AuditApiClient(vault_url)
                logger.debug("Audit trail enabled (Remote Vault)")
            except Exception as e:
                logger.warning(f"Audit trail setup failed: {e}")

        # Research graph
        try:
            from services.orchestrator.core.graph import compile_research_graph

            self._graph = compile_research_graph()
            logger.debug("Research graph compiled")
        except ImportError:
            logger.warning("Research graph not available")

    async def process_message(
        self,
        conversation_id: str,
        content: str,
        user_id: str,
        attachments: list[str] = None,
    ) -> ResearchResult:
        """
        Process a conversation message.

        Returns research result with content, sources, confidence.
        """
        start_time = datetime.utcnow()

        # 1. Classify query
        query_type = "research"
        bypass_research = False

        if self._classifier:
            classification = self._classifier.classify(content)
            # Handle both enum and string query_type
            qt = classification.query_type
            query_type = qt.value if hasattr(qt, "value") else str(qt)
            bypass_research = classification.bypass_graph

            logger.debug(f"Query classified as: {query_type}, bypass={bypass_research}")

        # 2. Check cache
        cache_key = f"research:{hash(content)}"
        cached_result = None

        if self._cache and not bypass_research:
            cached_result = await self._cache.get(cache_key)
            if cached_result:
                logger.debug("Cache hit for query")

                if self._audit:
                    await self._audit.log(
                        "CACHE_HIT",
                        action=f"Cache hit for: {content[:50]}",
                        actor=user_id,
                    )

                duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                return ResearchResult(
                    content=cached_result.get("content", ""),
                    confidence=cached_result.get("confidence", 0.8),
                    sources=cached_result.get("sources", []),
                    duration_ms=duration,
                    query_type=query_type,
                    was_cached=True,
                )

        # 3. Handle bypass cases (casual, utility)
        if bypass_research:
            result = await self._handle_bypass(content, query_type)

            if self._audit:
                await self._audit.log(
                    "QUERY_BYPASS",
                    action=f"Bypassed research: {query_type}",
                    actor=user_id,
                    details={"query_type": query_type},
                )

            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            result.duration_ms = duration
            return result

        # 4. Run research pipeline
        result = await self._run_research(content, user_id)

        # 5. Cache result
        if self._cache:
            config = get_environment_config()
            await self._cache.set(
                cache_key,
                {
                    "content": result.content,
                    "confidence": result.confidence,
                    "sources": result.sources,
                },
                ttl=config.cache_ttl_seconds,
            )

        # 6. Audit log
        if self._audit:
            await self._audit.log(
                "RESEARCH_COMPLETE",
                action=f"Research completed: {content[:50]}",
                actor=user_id,
                details={
                    "confidence": result.confidence,
                    "sources_count": len(result.sources),
                    "duration_ms": result.duration_ms,
                },
            )

        duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        result.duration_ms = duration

        return result

    async def _handle_bypass(self, content: str, query_type: str) -> ResearchResult:
        """Handle queries that bypass research."""

        if query_type == "casual":
            # Simple greeting response
            from services.orchestrator.core.query_classifier import CasualHandler

            handler = CasualHandler()
            response = await handler.handle(content)
            return ResearchResult(
                content=response,
                confidence=1.0,
                query_type=query_type,
            )

        elif query_type == "utility":
            # Translation, summarization, etc.
            from services.orchestrator.core.query_classifier import UtilityHandler

            handler = UtilityHandler()
            response = await handler.handle(content)
            return ResearchResult(
                content=response,
                confidence=0.9,
                query_type=query_type,
            )

        elif query_type == "unsafe":
            # Blocked query
            return ResearchResult(
                content="I cannot assist with that request.",
                confidence=1.0,
                query_type=query_type,
            )

        else:
            # Default fallback
            return ResearchResult(
                content="I'm not sure how to help with that.",
                confidence=0.5,
                query_type=query_type,
            )

    async def _run_research(self, content: str, user_id: str) -> ResearchResult:
        """Run the full research pipeline.

        v4.1: Uses kernel pipeline (KernelCell with cognitive cycle) when
        USE_KERNEL_PIPELINE is enabled. Falls back to legacy LangGraph graph.
        """
        import os

        use_kernel = os.getenv("USE_KERNEL_PIPELINE", "true").lower() in (
            "true",
            "1",
            "yes",
        )

        # ── Kernel Pipeline ───────────────────────────────────────────
        if use_kernel:
            try:
                from services.orchestrator.core.kernel_cell import run_kernel
                from services.orchestrator.core.response_formatter import (
                    envelope_to_chat_response,
                )
                from services.orchestrator.core.tool_bridge import create_tool_executor

                tool_executor = create_tool_executor(query=content)

                envelope = await run_kernel(
                    query=content,
                    tool_executor=tool_executor,
                    level="manager",
                    domain="research",
                )

                result = envelope_to_chat_response(envelope)

                return ResearchResult(
                    content=result.get("content", ""),
                    confidence=result.get("confidence", 0.0),
                    sources=result.get("sources", []),
                    tool_calls=result.get("tool_calls", []),
                    facts=result.get("facts", []),
                    query_type="kernel",
                )

            except Exception as e:
                logger.error(f"Kernel pipeline error: {e}")
                logger.info("Falling back to legacy graph pipeline")

        # ── Legacy Graph Pipeline (fallback) ──────────────────────────
        if not self._graph:
            return await self._fallback_research(content)

        try:
            from services.orchestrator.core.graph import GraphState

            initial_state = GraphState(
                query=content,
                current_depth=0,
                max_depth=2,
            )

            final_state = await self._graph.ainvoke(initial_state)

            return ResearchResult(
                content=final_state.get("final_report", ""),
                confidence=final_state.get("confidence", 0.0),
                sources=final_state.get("sources", []),
                tool_calls=final_state.get("tool_calls", []),
                facts=final_state.get("facts", []),
                query_type="research",
            )

        except Exception as e:
            logger.error(f"Research pipeline error: {e}")
            return await self._fallback_research(content)

    async def _fallback_research(self, content: str) -> ResearchResult:
        """Fallback when graph is not available."""
        try:
            from shared.llm import chat_completion

            response = await chat_completion(
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant."},
                    {"role": "user", "content": content},
                ],
                stream=False,
            )

            return ResearchResult(
                content=response.get("content", ""),
                confidence=0.6,
                query_type="fallback",
            )

        except Exception as e:
            logger.error(f"Fallback research error: {e}")
            return ResearchResult(
                content="I encountered an error processing your request.",
                confidence=0.0,
                query_type="error",
            )

    async def process_and_store(
        self,
        conversation_id: str,
        content: str,
        user_id: str,
        attachments: list[str] = None,
    ) -> Message:
        """
        Process message and store response in conversation.

        Returns the assistant message.
        """
        manager = await get_conversation_manager()

        # Get conversation
        conv = await manager.get_conversation(conversation_id)
        if not conv:
            raise ValueError(f"Conversation not found: {conversation_id}")

        # Process
        result = await self.process_message(conversation_id, content, user_id, attachments)

        # Store assistant response
        assistant_msg = await manager.add_message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=result.content,
            sources=result.sources,
            tool_calls=result.tool_calls,
            confidence=result.confidence,
        )

        return assistant_msg

    async def stream_message(
        self,
        conversation_id: str,
        content: str,
        user_id: str,
    ) -> AsyncIterator[dict]:
        """
        Stream research results.

        Yields events like:
        - {"type": "status", "data": "Classifying..."}
        - {"type": "chunk", "data": "partial content"}
        - {"type": "source", "data": {...}}
        - {"type": "done", "data": {...}}
        """
        yield {"type": "status", "data": "Processing query..."}

        # Classify
        if self._classifier:
            yield {"type": "status", "data": "Classifying query..."}
            classification = self._classifier.classify(content)
            qt = classification.query_type
            yield {"type": "classification", "data": qt.value if hasattr(qt, "value") else str(qt)}

        # Check cache
        if self._cache:
            yield {"type": "status", "data": "Checking cache..."}

        # Run research
        yield {"type": "status", "data": "Researching..."}

        result = await self.process_message(conversation_id, content, user_id)

        # Stream content in chunks
        chunk_size = 100
        for i in range(0, len(result.content), chunk_size):
            yield {"type": "chunk", "data": result.content[i : i + chunk_size]}
            await asyncio.sleep(0.02)  # Simulate streaming

        # Send sources
        for source in result.sources:
            yield {"type": "source", "data": source}

        # Done
        yield {
            "type": "done",
            "data": {
                "confidence": result.confidence,
                "sources_count": len(result.sources),
                "duration_ms": result.duration_ms,
                "was_cached": result.was_cached,
            },
        }


# ============================================================================
# Singleton
# ============================================================================

_pipeline: ConversationResearchPipeline | None = None


async def get_research_pipeline() -> ConversationResearchPipeline:
    """Get singleton research pipeline."""
    global _pipeline
    if _pipeline is None:
        _pipeline = ConversationResearchPipeline()
        await _pipeline.initialize()
    return _pipeline
