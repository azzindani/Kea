"""
Generator Agent.

The Optimist - generates comprehensive answers from facts.
"""

from __future__ import annotations

from shared.llm import LLMConfig, OpenRouterProvider
from shared.llm.provider import LLMMessage, LLMRole
from shared.logging import get_logger
from shared.prompts import get_agent_prompt

logger = get_logger(__name__)


class GeneratorAgent:
    """
    The Generator (Optimist) Agent.

    Role: Generate comprehensive, well-structured answers from collected facts.
    Personality: Optimistic, thorough, constructive.
    """

    def __init__(self):
        self.name = "Generator"
        self.role = "The Optimist"
        self.system_prompt = get_agent_prompt("generator")

    async def _get_knowledge_context(self, query: str) -> str:
        """Retrieve domain-specific knowledge for the query."""
        try:
            from shared.knowledge.retriever import get_knowledge_retriever

            retriever = get_knowledge_retriever()
            import asyncio

            context = await asyncio.wait_for(
                retriever.retrieve_skills(query, limit=2),
                timeout=3.0,
            )
            return context
        except Exception:
            return ""

    async def generate(
        self, query: str, facts: list, sources: list, revision_feedback: str = None
    ) -> str:
        """
        Generate a comprehensive answer from facts.

        Args:
            query: Research question
            facts: Collected facts
            sources: Source references

        Returns:
            Generated answer text
        """
        logger.info(f"Generator: Processing {len(facts)} facts")

        try:
            import os

            if not os.getenv("OPENROUTER_API_KEY"):
                return self._fallback_generate(query, facts, sources)

            provider = OpenRouterProvider()
            from shared.config import get_settings

            config = LLMConfig(
                model=get_settings().models.generator_model,
                temperature=0.6,
                max_tokens=32768,
            )

            # Retrieve domain knowledge to enhance generation
            knowledge_context = await self._get_knowledge_context(query)
            if knowledge_context:
                logger.info(
                    f"Generator: Injecting {len(knowledge_context)} chars of domain knowledge into system prompt"
                )
            else:
                logger.debug("Generator: No domain knowledge retrieved — using base system prompt")

            # Format facts with full tool call schema as citation
            facts_text = ""
            for idx, f in enumerate(facts):
                if isinstance(f, dict):
                    text = f.get("text", str(f))
                    citation = f.get("tool_citation")
                    if citation and isinstance(citation, dict):
                        t_name = citation.get("tool_name", "unknown")
                        server = citation.get("server_name", "unknown")
                        dur = citation.get("duration_ms", 0.0)
                        ts = citation.get("invoked_at", "")
                        url = citation.get("source_url", "")
                        args = citation.get("arguments", {})
                        args_str = (
                            ", ".join(f"{k}={str(v)[:40]!r}" for k, v in list(args.items())[:5])
                            if args
                            else "no args"
                        )
                        url_part = f" | url={url}" if url else ""
                        facts_text += (
                            f"[Fact #{idx + 1}] {text}\n"
                            f"  [TOOL CALL] tool={t_name}({args_str}) | server={server} | "
                            f"{dur:.0f}ms | {ts}{url_part}\n\n"
                        )
                    else:
                        source_url = f.get("source_url", "unknown")
                        tool = f.get("source", "unknown")
                        facts_text += (
                            f"[Fact #{idx + 1}] {text}\n  Source: {source_url} (via {tool})\n\n"
                        )
                else:
                    facts_text += f"[Fact #{idx + 1}] {str(f)}\n  Source: unknown\n\n"

            if not facts_text:
                facts_text = "No facts available"

            # Format sources list
            sources_text = (
                "\n".join(
                    [f"- {s.get('url', 'unknown')} ({s.get('tool', 'unknown')})" for s in sources]
                )
                if sources
                else "No sources available"
            )

            # Add revision feedback if this is a revision
            revision_context = ""
            if revision_feedback:
                revision_context = f"""

⚠️ REVISION REQUESTED
The Critic identified issues with your previous answer. Address these points:

{revision_feedback}

You MUST fix these issues in your revised answer."""

            # Build enhanced system prompt with domain knowledge
            system_prompt = self.system_prompt
            if knowledge_context:
                system_prompt += f"\n\n{knowledge_context}"

            messages = [
                LLMMessage(role=LLMRole.SYSTEM, content=system_prompt),
                LLMMessage(
                    role=LLMRole.USER,
                    content=f"""Research Question: {query}

Available Facts (with source URLs):
{facts_text}

Available Sources:
{sources_text}
{revision_context}

Generate a comprehensive answer that:
1. Directly addresses the question
2. Uses ONLY the available facts above
3. CITES source URLs for EVERY numerical claim using [Source: URL] format
4. Identifies any gaps in information
5. Provides a confidence assessment

CRITICAL: Every fact, statistic, or number MUST be followed by [Source: URL].""",
                ),
            ]

            response = await provider.complete(messages, config)

            logger.info(f"Generator: Answer generated ({len(response.content)} chars)")
            return response.content

        except Exception as e:
            logger.error(f"Generator error: {e}")
            return self._fallback_generate(query, facts, sources)

    def _fallback_generate(self, query: str, facts: list, sources: list) -> str:
        """Fallback generation without LLM."""
        return f"""## Response to: {query}

Based on {len(facts)} collected facts from {len(sources)} sources:

{chr(10).join([f"- {str(f)[:100]}" for f in facts[:5]])}

Note: Full generation requires LLM integration."""
