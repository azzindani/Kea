"""
Critic Agent.

The Pessimist - challenges assumptions and finds weaknesses.
"""

from __future__ import annotations

from shared.llm import LLMConfig, OpenRouterProvider
from shared.llm.provider import LLMMessage, LLMRole
from shared.logging import get_logger
from shared.prompts import get_agent_prompt

logger = get_logger(__name__)


class CriticAgent:
    """
    The Critic (Pessimist) Agent.

    Role: Challenge assumptions, find weaknesses, identify gaps.
    Personality: Skeptical, thorough, constructive critic.
    """

    def __init__(self):
        self.name = "Critic"
        self.role = "The Pessimist"
        self.system_prompt = get_agent_prompt("critic")

    async def _get_knowledge_context(self, query: str) -> str:
        """Retrieve domain-specific rules and knowledge for critique."""
        try:
            import asyncio

            from shared.knowledge.retriever import get_knowledge_retriever

            retriever = get_knowledge_retriever()
            context = await asyncio.wait_for(
                retriever.retrieve_all(query, skill_limit=1, rule_limit=2),
                timeout=3.0,
            )
            return context
        except Exception:
            return ""

    async def critique(self, answer: str, facts: list, sources: list, query: str = "") -> str:
        """
        Critique a generated answer.

        Args:
            answer: The Generator's answer
            facts: Available facts
            sources: Source references
            query: Original research query (for knowledge retrieval)

        Returns:
            Critique with specific feedback
        """
        logger.info("Critic: Analyzing answer")

        try:
            import os

            if not os.getenv("OPENROUTER_API_KEY"):
                return self._fallback_critique(answer)

            provider = OpenRouterProvider()
            from shared.config import get_settings

            config = LLMConfig(
                model=get_settings().models.critic_model,
                temperature=0.4,
                max_tokens=32768,
            )

            # Retrieve domain knowledge (especially rules) for informed critique
            knowledge_context = await self._get_knowledge_context(query or answer[:200])
            system_prompt = self.system_prompt
            if knowledge_context:
                system_prompt += f"\n\n{knowledge_context}"
                logger.info(
                    f"Critic: Injecting {len(knowledge_context)} chars of domain knowledge into system prompt"
                )
            else:
                logger.debug("Critic: No domain knowledge retrieved   using base system prompt")

            messages = [
                LLMMessage(role=LLMRole.SYSTEM, content=system_prompt),
                LLMMessage(
                    role=LLMRole.USER,
                    content=f"""Critique this answer:

{answer[:1500]}

Based on {len(facts)} facts from {len(sources)} sources.

Provide:
1. Strengths (what's good)
2. Weaknesses (what's problematic)
3. Missing elements
4. Suggestions for improvement""",
                ),
            ]

            response = await provider.complete(messages, config)

            logger.info(f"Critic: Critique complete ({len(response.content)} chars):\n{response.content[:2000]}")
            return response.content

        except Exception as e:
            logger.error(f"Critic error: {e}")
            return self._fallback_critique(answer)

    def _fallback_critique(self, answer: str) -> str:
        """Fallback critique without LLM."""
        return f"""## Critique

Answer length: {len(answer)} characters

Observations:
- Answer reviewed for basic structure
- Source citations: {"Present" if "source" in answer.lower() else "Missing"}
- Confidence stated: {"Yes" if "confidence" in answer.lower() else "No"}

Note: Full critique requires LLM integration."""
