"""
Synthesizer Node.

Generates final research reports from collected facts.
"""

from __future__ import annotations

from typing import Any

from shared.llm import LLMConfig, OpenRouterProvider
from shared.llm.provider import LLMMessage, LLMRole
from shared.logging import get_logger
from shared.prompts import get_agent_prompt

logger = get_logger(__name__)


async def synthesizer_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Synthesizer node: Generate final report from facts.

    Takes all collected facts and sources and synthesizes them into:
    - Executive summary
    - Key findings
    - Supporting evidence
    - Confidence assessment

    Args:
        state: Current graph state with 'facts', 'sources'

    Returns:
        Updated state with 'report', 'confidence'
    """
    logger.info("Synthesizer: Creating final report")

    query = state.get("query", "")
    facts = state.get("facts", [])
    sources = state.get("sources", [])
    generator_output = state.get("generator_output", "")

    # Retrieve domain knowledge for synthesis
    knowledge_context = ""
    try:
        import asyncio

        from shared.knowledge.retriever import get_knowledge_retriever

        retriever = get_knowledge_retriever()
        knowledge_context = await asyncio.wait_for(
            retriever.retrieve_skills(query, limit=2),
            timeout=3.0,
        )
        if knowledge_context:
            logger.info(
                f"Synthesizer: Retrieved {len(knowledge_context)} chars of domain knowledge"
            )
    except Exception as e:
        logger.debug(f"Synthesizer: Knowledge retrieval skipped ({e})")

    try:
        import os

        if os.getenv("OPENROUTER_API_KEY"):
            from shared.config import get_settings

            config_settings = get_settings()

            provider = OpenRouterProvider()
            config = LLMConfig(
                model=config_settings.models.default_model,
                temperature=0.5,
                max_tokens=32768,
            )

            # Prepare facts summary
            facts_text = (
                "\n".join(
                    [
                        f"- {f.get('text', str(f)) if isinstance(f, dict) else str(f)}"
                        for f in facts  # No limit - use all facts
                    ]
                )
                if facts
                else "No facts collected"
            )

            sources_text = (
                "\n".join(
                    [
                        f"- {s.get('url', str(s)) if isinstance(s, dict) else str(s)}"
                        for s in sources  # No limit - use all sources
                    ]
                )
                if sources
                else "No sources"
            )

            # Build knowledge-enhanced system prompt
            knowledge_section = ""
            if knowledge_context:
                knowledge_section = f"""

{knowledge_context}

Apply the above domain expertise when structuring the report.
Use the reasoning frameworks and output standards to ensure
domain-appropriate analysis and formatting."""

            messages = [
                LLMMessage(
                    role=LLMRole.SYSTEM,
                    content=get_agent_prompt("synthesizer") + knowledge_section,
                ),
                LLMMessage(
                    role=LLMRole.USER,
                    content=f"""Create a research report for:

Query: {query}

Collected Facts:
{facts_text}

Sources:
{sources_text}

Previous Analysis:
{generator_output[:500] if generator_output else "None"}""",
                ),
            ]

            response = await provider.complete(messages, config)

            state["report"] = response.content

            # Calculate confidence using reranker scoring (decimal precision)
            try:
                from shared.embedding.model_manager import get_reranker_provider

                if facts:
                    reranker = get_reranker_provider()
                    fact_texts = [
                        f.get("text", str(f)) if isinstance(f, dict) else str(f)
                        for f in facts[:100]
                    ]
                    results = await reranker.rerank(query, fact_texts)
                    if results:
                        avg_score = sum(r.score for r in results) / len(results)
                        state["confidence"] = round(avg_score, 4)  # Precise decimal
                    else:
                        state["confidence"] = 0.5
                else:
                    state["confidence"] = 0.0
            except Exception as e:
                logger.warning(f"Reranker confidence failed: {e}, falling back to text")
                # Fallback to text parsing
                if "high" in response.content.lower():
                    state["confidence"] = 0.85
                elif "medium" in response.content.lower():
                    state["confidence"] = 0.65
                else:
                    state["confidence"] = 0.45

            logger.info(f"Synthesizer: Report generated ({len(response.content)} chars)")

        else:
            # Fallback without LLM
            state["report"] = f"""## Research Report

Query: {query}

Facts Collected: {len(facts)}
Sources Used: {len(sources)}

Note: Full synthesis requires LLM integration."""
            state["confidence"] = 0.5

    except Exception as e:
        logger.error(f"Synthesizer error: {e}")
        state["report"] = f"Error generating report: {e}"
        state["confidence"] = 0.0

    state["status"] = "complete"
    return state
