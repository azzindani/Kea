"""
Divergence Engine Node.

Generates alternative hypotheses and performs abductive reasoning.
"""

from __future__ import annotations

from typing import Any
from shared.logging import get_logger
from shared.llm import OpenRouterProvider, LLMConfig
from shared.llm.provider import LLMMessage, LLMRole

logger = get_logger(__name__)


async def divergence_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Divergence Engine: Generate alternative hypotheses.
    
    Performs abductive reasoning to:
    - Generate alternative explanations
    - Identify potential biases
    - Suggest counter-hypotheses
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with alternative hypotheses
    """
    logger.info("Divergence: Generating alternative hypotheses")
    
    query = state.get("query", "")
    facts = state.get("facts", [])
    hypotheses = state.get("hypotheses", [])
    
    try:
        import os
        if os.getenv("OPENROUTER_API_KEY"):
            provider = OpenRouterProvider()
            from shared.config import get_settings
            config = LLMConfig(
                model=get_settings().models.default_model,
                temperature=0.8,  # Higher for creativity
                max_tokens=32768,
            )
            
            facts_text = "\n".join([str(f)[:100] for f in facts[:5]])
            hypotheses_text = "\n".join(hypotheses[:3]) if hypotheses else "None yet"
            
            messages = [
                LLMMessage(
                    role=LLMRole.SYSTEM,
                    content="""You are a devil's advocate. Challenge assumptions and propose alternatives.

For each hypothesis, provide:
1. A counter-hypothesis
2. Potential bias in the original
3. Missing perspective"""
                ),
                LLMMessage(
                    role=LLMRole.USER,
                    content=f"""Query: {query}

Current Hypotheses:
{hypotheses_text}

Facts Collected:
{facts_text}

Generate alternative perspectives and counter-hypotheses."""
                )
            ]
            
            response = await provider.complete(messages, config)
            
            # Add alternatives to state
            state["alternative_hypotheses"] = response.content
            state["divergence_complete"] = True
            
            logger.info("Divergence: Alternative hypotheses generated")
            
        else:
            state["alternative_hypotheses"] = ""
            state["divergence_complete"] = True
            
    except Exception as e:
        logger.error(f"Divergence error: {e}")
        state["alternative_hypotheses"] = ""
        state["divergence_complete"] = True
    
    return state
