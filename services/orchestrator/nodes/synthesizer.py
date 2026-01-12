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
            provider = OpenRouterProvider()
            config = LLMConfig(
                model="nvidia/nemotron-3-nano-30b-a3b:free",
                temperature=0.5,
                max_tokens=1000,
            )
            
            # Prepare facts summary
            facts_text = "\n".join([
                f"- {f.get('text', str(f)) if isinstance(f, dict) else str(f)}"
                for f in facts[:20]  # Limit to avoid token overflow
            ]) if facts else "No facts collected"
            
            sources_text = "\n".join([
                f"- {s.get('url', str(s)) if isinstance(s, dict) else str(s)}"
                for s in sources[:10]
            ]) if sources else "No sources"
            
            messages = [
                LLMMessage(
                    role=LLMRole.SYSTEM,
                    content="""You are a research report synthesizer. Create concise, well-structured reports.

Format:
## Executive Summary
[2-3 sentences]

## Key Findings
1. [Finding with evidence]
2. [Finding with evidence]

## Confidence Assessment
[High/Medium/Low with justification]

## Sources
[List sources used]"""
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
            
            # Extract confidence from report
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
