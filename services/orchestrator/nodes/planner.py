"""
Planner Node.

Decomposes research queries into sub-queries and hypotheses.
"""

from __future__ import annotations

from typing import Any
from shared.logging import get_logger
from shared.llm import OpenRouterProvider, LLMConfig
from shared.llm.provider import LLMMessage, LLMRole

logger = get_logger(__name__)


async def planner_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Planner node: Decompose query into sub-queries.
    
    Takes a complex research query and breaks it down into:
    - Sub-queries (atomic research questions)
    - Hypotheses (testable claims)
    - Required data sources
    
    Args:
        state: Current graph state with 'query'
        
    Returns:
        Updated state with 'sub_queries', 'hypotheses'
    """
    logger.info("Planner: Decomposing query", extra={"query": state.get("query", "")[:100]})
    
    query = state.get("query", "")
    
    # Use LLM to decompose query
    try:
        import os
        if os.getenv("OPENROUTER_API_KEY"):
            provider = OpenRouterProvider()
            config = LLMConfig(
                model="nvidia/nemotron-3-nano-30b-a3b:free",
                temperature=0.3,
                max_tokens=500,
            )
            
            messages = [
                LLMMessage(
                    role=LLMRole.SYSTEM,
                    content="""You are a research planner. Decompose queries into sub-questions.
Output format:
SUB-QUERIES:
1. [question]
2. [question]

HYPOTHESES:
1. [testable claim]
2. [testable claim]"""
                ),
                LLMMessage(role=LLMRole.USER, content=f"Decompose this research query:\n\n{query}")
            ]
            
            response = await provider.complete(messages, config)
            
            # Parse response
            sub_queries = []
            hypotheses = []
            
            lines = response.content.split("\n")
            current_section = None
            
            for line in lines:
                line = line.strip()
                if "SUB-QUERIES" in line.upper():
                    current_section = "sub_queries"
                elif "HYPOTHESES" in line.upper():
                    current_section = "hypotheses"
                elif line and line[0].isdigit() and "." in line:
                    text = line.split(".", 1)[1].strip() if "." in line else line
                    if current_section == "sub_queries":
                        sub_queries.append(text)
                    elif current_section == "hypotheses":
                        hypotheses.append(text)
            
            state["sub_queries"] = sub_queries or [query]
            state["hypotheses"] = hypotheses
            
            logger.info(f"Planner: Generated {len(sub_queries)} sub-queries, {len(hypotheses)} hypotheses")
            
        else:
            # Fallback without LLM
            state["sub_queries"] = [query]
            state["hypotheses"] = []
            logger.info("Planner: No LLM, using query as-is")
            
    except Exception as e:
        logger.error(f"Planner error: {e}")
        state["sub_queries"] = [query]
        state["hypotheses"] = []
    
    state["status"] = "planning_complete"
    return state
