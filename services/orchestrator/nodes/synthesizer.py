"""
Synthesizer Node.

Generates final research reports from collected facts.
"""

from __future__ import annotations

from typing import Any
from shared.logging import get_logger
from shared.llm import OpenRouterProvider, LLMConfig
from shared.llm.provider import LLMMessage, LLMRole

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
            facts_text = "\n".join([
                f"- {f.get('text', str(f)) if isinstance(f, dict) else str(f)}"
                for f in facts  # No limit - use all facts
            ]) if facts else "No facts collected"
            
            sources_text = "\n".join([
                f"- {s.get('url', str(s)) if isinstance(s, dict) else str(s)}"
                for s in sources  # No limit - use all sources
            ]) if sources else "No sources"
            
            messages = [
                LLMMessage(
                    role=LLMRole.SYSTEM,
                    content="""You are a research report synthesizer. Create concise, well-structured reports.

CRITICAL RULES - NEVER VIOLATE THESE:
1. ONLY use information explicitly provided in "Collected Facts" and "Sources"
2. NEVER fabricate, invent, or guess any data (numbers, dates, names, statistics)
3. If facts are incomplete or missing, explicitly state "Data not collected/available"
4. If a task shows as "Not yet executed", say so - DO NOT make up results
5. If numbers or statistics are not in the facts, say "Specific figures not obtained"
6. Distinguish clearly between what WAS found vs what was PLANNED but not executed

Format:
## Executive Summary
[2-3 sentences based ONLY on collected facts]

## What Was Accomplished
[List tasks that ACTUALLY completed with real data obtained]

## What Is Still Pending
[List tasks that were planned but NOT executed - do NOT fabricate results for these]

## Key Findings (from actual data only)
1. [Finding with evidence from facts]
2. [Finding with evidence from facts]

## Data Gaps
[Explicitly list what data is missing or was not collected]

## Confidence Assessment
[High/Medium/Low with justification - Low if many data gaps]

## Sources
[List only actual sources used]"""
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
{generator_output[:500] if generator_output else 'None'}"""
                )
            ]
            
            response = await provider.complete(messages, config)
            
            state["report"] = response.content
            
            # Calculate confidence using reranker scoring (decimal precision)
            try:
                from shared.embedding.model_manager import get_reranker_provider
                if facts:
                    reranker = get_reranker_provider()
                    fact_texts = [f.get('text', str(f)) if isinstance(f, dict) else str(f) for f in facts[:100]]
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
