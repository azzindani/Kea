"""
Keeper Node.

The Context Guard - monitors for drift and determines when to stop.
"""

from __future__ import annotations

from typing import Any
from shared.logging import get_logger

logger = get_logger(__name__)


async def keeper_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Keeper node: Monitor context drift and determine continuation.
    
    The Keeper is responsible for:
    - Detecting when research has drifted from original query
    - Determining if enough information has been gathered
    - Deciding whether to continue or stop the research loop
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with 'should_continue' decision
    """
    logger.info("Keeper: Checking context drift")
    
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 3)
    query = state.get("query", "")
    facts = state.get("facts", [])
    
    # Check iteration limit
    if iteration >= max_iterations:
        logger.info(f"Keeper: Max iterations ({max_iterations}) reached")
        state["should_continue"] = False
        return state
    
    # Check if we have enough facts
    min_facts = 3
    if len(facts) >= min_facts:
        logger.info(f"Keeper: Sufficient facts gathered ({len(facts)} >= {min_facts})")
        # Could continue for more depth, or stop
        if iteration >= 2:
            state["should_continue"] = False
            return state
    
    # Check for context drift (simplified - in production use embeddings)
    if facts:
        # Simple keyword overlap check
        query_words = set(query.lower().split())
        relevant_facts = 0
        
        for fact in facts:
            fact_text = str(fact).lower() if isinstance(fact, dict) else fact.lower()
            fact_words = set(fact_text.split())
            overlap = len(query_words & fact_words)
            if overlap > 0:
                relevant_facts += 1
        
        relevance_ratio = relevant_facts / len(facts) if facts else 0
        
        if relevance_ratio < 0.3 and iteration > 0:
            logger.warning(f"Keeper: Context drift detected (relevance: {relevance_ratio:.2f})")
            state["should_continue"] = False
            state["drift_detected"] = True
            return state
    
    # Continue research
    state["should_continue"] = True
    state["iteration"] = iteration + 1
    
    logger.info(f"Keeper: Continuing research (iteration {iteration + 1})")
    return state
