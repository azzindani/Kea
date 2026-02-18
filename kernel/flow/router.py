"""
Intention Router.

Classifies research queries into Path A/B/C/D.
"""

from __future__ import annotations

from typing import Any, Literal

from shared.llm import LLMConfig, OpenRouterProvider
from shared.llm.provider import LLMMessage, LLMRole
from shared.logging import get_logger
from shared.prompts import get_agent_prompt
from shared.vocab import load_vocab
from shared.embedding.model_manager import get_embedding_provider
from kernel.logic.signal_bus import emit_signal, SignalType

logger = get_logger(__name__)


PathType = Literal["A", "B", "C", "D"]


class IntentionRouter:
    """
    Routes research queries to appropriate processing paths.

    Paths:
    - A: Memory Fork (Incremental) - Has prior context
    - B: Shadow Lab (Recalculation) - Verification needed
    - C: Grand Synthesis (Meta-analysis) - Multiple sources
    - D: Deep Research (Zero-shot) - New topic
    """

    # Semantic Examples for Centroids
    PATH_EXAMPLES = {
        "A": [
            "Expand on the previous research",
            "Deep dive into the second point",
            "Continue the analysis of X",
            "Follow up on the earnings report",
            "Update the previous findings",
        ],
        "B": [
            "Verify these figures",
            "Fact check the claims",
            "Validate the sources",
            "Audit the calculations",
            "Check for errors in the report",
        ],
        "C": [
            "Compare Apple and Microsoft",
            "Synthesize findings from these reports",
            "Meta-analysis of AI trends",
            "Aggregate data from Q1-Q4",
            "Benchmark performance across sectors",
        ],
        "D": [
            "Research the market for electric vehicles",
            "Find information about quantum computing",
            "Overview of the biotech industry",
            "What is the latest on generative AI?",
            "Analyze the competitive landscape of X",
        ],
    }
    
    _centroids: dict[str, list[float]] = {}
    _embedding_provider = None

    def __init__(self):
        self.system_prompt = get_agent_prompt("router")

    async def route(self, query: str, context: dict[str, Any] | None = None) -> PathType:
        """
        Route a query to the appropriate path.

        Args:
            query: Research query
            context: Optional context about prior research

        Returns:
            Path letter (A/B/C/D)
        """
        logger.info("Router: Analyzing query")

        # Quick heuristics first
        path = self._heuristic_route(query, context)
        if path:
            logger.info(f"Router: Heuristic path = {path}")
            try:
                emit_signal(SignalType.ROUTING, "IntentionRouter", path, 0.7, method="heuristic")
            except Exception: pass
            return path
            
        # Semantic Routing (v2.0)
        path, confidence = await self._semantic_route(query)
        if path and confidence > 0.65:
            logger.info(f"Router: Semantic path = {path} (conf={confidence:.2f})")
            try:
                emit_signal(SignalType.ROUTING, "IntentionRouter", path, confidence, method="semantic")
            except Exception: pass
            return path

        # Use LLM for complex cases
        try:
            import os

            if os.getenv("OPENROUTER_API_KEY"):
                provider = OpenRouterProvider()
                from shared.config import get_settings

                config = LLMConfig(
                    model=get_settings().models.planner_model,
                    temperature=0.1,
                    max_tokens=10,
                )

                context_info = ""
                if context:
                    if context.get("prior_research"):
                        context_info = "Has prior research context."
                    if context.get("data_to_verify"):
                        context_info += " Has data needing verification."

                messages = [
                    LLMMessage(role=LLMRole.SYSTEM, content=self.system_prompt),
                    LLMMessage(
                        role=LLMRole.USER,
                        content=f"Query: {query}\nContext: {context_info or 'None'}",
                    ),
                ]

                response = await provider.complete(messages, config)

                # Extract path letter
                for char in response.content.upper():
                    if char in "ABCD":
                        logger.info(f"Router: LLM path = {char}")
                        try:
                            emit_signal(SignalType.ROUTING, "IntentionRouter", char, 0.9, method="llm")
                        except Exception: pass
                        return char

        except Exception as e:
            logger.error(f"Router error: {e}")

        # Default to Deep Research
        logger.info("Router: Defaulting to path D")
        try:
            emit_signal(SignalType.ROUTING, "IntentionRouter", "D", 0.0, method="default")
        except Exception: pass
        return "D"

    def _heuristic_route(self, query: str, context: dict | None) -> PathType | None:
        """Quick heuristic routing."""
        query_lower = query.lower()

        kw = load_vocab("classification").get("routing_keywords", {})

        # Path C indicators (meta-analysis)
        if any(word in query_lower for word in kw.get("path_c", [])):
            return "C"

        # Path B indicators (verification)
        if any(word in query_lower for word in kw.get("path_b", [])):
            return "B"

        # Path A indicators (incremental)
        if context and context.get("prior_research"):
            if any(word in query_lower for word in kw.get("path_a", [])):
                return "A"

        return None

    async def _get_provider(self):
        if self._embedding_provider is None:
            self._embedding_provider = get_embedding_provider()
        return self._embedding_provider

    async def _ensure_centroids(self):
        if self._centroids:
            return

        # Phase 7: Load from Vault
        try:
            from shared.knowledge.retriever import get_knowledge_retriever
            retriever = get_knowledge_retriever()
            
            vault_items = await retriever.search_raw(
                query="router",
                limit=10, 
                domain="kernel", 
                category="example"
            )
            
            if vault_items:
                logger.info(f"Router: Loaded {len(vault_items)} example sets from Vault")
                for item in vault_items:
                    meta = item.get("metadata", {})
                    examples = meta.get("list", [])
                    if examples:
                        # Extract path from tag (e.g. router_path_a -> A)
                        tags = item.get("tags", [])
                        for t in tags:
                            if t.startswith("router_path_"):
                                path_key = t.replace("router_path_", "").upper()
                                if path_key in self.PATH_EXAMPLES:
                                    self.PATH_EXAMPLES[path_key] = examples
        except Exception as e:
            logger.warning(f"Failed to load router examples from Vault: {e}")

        try:
            provider = await self._get_provider()
            for path, examples in self.PATH_EXAMPLES.items():
                embeddings = await provider.embed(examples)
                if not embeddings:
                    continue
                    
                # Compute centroid
                dim = len(embeddings[0])
                centroid = [0.0] * dim
                for emb in embeddings:
                    for i in range(dim):
                        centroid[i] += emb[i]
                
                # Normalize
                count = len(embeddings)
                magnitude = 0.0
                for i in range(dim):
                    centroid[i] /= count
                    magnitude += centroid[i] ** 2
                
                magnitude = magnitude ** 0.5
                if magnitude > 0:
                    for i in range(dim):
                        centroid[i] /= magnitude
                        
                self._centroids[path] = centroid
        except Exception as e:
            logger.warning(f"Failed to compute router centroids: {e}")

    async def _semantic_route(self, query: str) -> tuple[PathType | None, float]:
        """Route based on embedding similarity."""
        try:
            await self._ensure_centroids()
            if not self._centroids:
                return None, 0.0
                
            provider = await self._get_provider()
            query_emb = await provider.embed_query(query)
            
            best_path = None
            best_score = -1.0
            
            for path, centroid in self._centroids.items():
                score = sum(a * b for a, b in zip(query_emb, centroid))
                if score > best_score:
                    best_score = score
                    best_path = path
            
            return best_path, best_score
            
        except Exception as e:
            logger.debug(f"Semantic routing failed: {e}")
            return None, 0.0


async def router_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node for routing."""
    router = IntentionRouter()

    context = {
        "prior_research": state.get("prior_research"),
        "data_to_verify": state.get("data_to_verify"),
    }

    path = await router.route(state.get("query", ""), context)
    state["path"] = path

    logger.info(f"Router: Selected path {path}")
    return state
