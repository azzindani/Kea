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
                        return char

        except Exception as e:
            logger.error(f"Router error: {e}")

        # Default to Deep Research
        logger.info("Router: Defaulting to path D")
        return "D"

    def _heuristic_route(self, query: str, context: dict | None) -> PathType | None:
        """Quick heuristic routing."""
        query_lower = query.lower()

        # Path C indicators (meta-analysis)
        if any(
            word in query_lower
            for word in ["compare", "meta-analysis", "across", "review of studies"]
        ):
            return "C"

        # Path B indicators (verification)
        if any(word in query_lower for word in ["verify", "check", "validate", "recalculate"]):
            return "B"

        # Path A indicators (incremental)
        if context and context.get("prior_research"):
            if any(
                word in query_lower for word in ["follow up", "continue", "more about", "expand on"]
            ):
                return "A"

        return None


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
