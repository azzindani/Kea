"""
Critic Agent.

The Pessimist - challenges assumptions and finds weaknesses.
"""

from __future__ import annotations

from typing import Any
from shared.logging import get_logger
from shared.llm import OpenRouterProvider, LLMConfig
from shared.llm.provider import LLMMessage, LLMRole

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
        self.system_prompt = """You are the Critic - a skeptical fact-checker.

Your role:
- Identify weaknesses in arguments
- Challenge unsupported claims
- Find logical fallacies
- Question source reliability
- Suggest what's missing

Be constructive - don't just criticize, suggest improvements."""
    
    async def critique(self, answer: str, facts: list, sources: list) -> str:
        """
        Critique a generated answer.
        
        Args:
            answer: The Generator's answer
            facts: Available facts
            sources: Source references
            
        Returns:
            Critique with specific feedback
        """
        logger.info("Critic: Analyzing answer")
        
        try:
            import os
            if not os.getenv("OPENROUTER_API_KEY"):
                return self._fallback_critique(answer)
            
            provider = OpenRouterProvider()
            config = LLMConfig(
                model="nvidia/nemotron-3-nano-30b-a3b:free",
                temperature=0.4,
                max_tokens=600,
            )
            
            messages = [
                LLMMessage(role=LLMRole.SYSTEM, content=self.system_prompt),
                LLMMessage(
                    role=LLMRole.USER,
                    content=f"""Critique this answer:

{answer[:1500]}

Based on {len(facts)} facts from {len(sources)} sources.

Provide:
1. Strengths (what's good)
2. Weaknesses (what's problematic)
3. Missing elements
4. Suggestions for improvement"""
                )
            ]
            
            response = await provider.complete(messages, config)
            
            logger.info(f"Critic: Critique complete ({len(response.content)} chars)")
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
- Source citations: {'Present' if 'source' in answer.lower() else 'Missing'}
- Confidence stated: {'Yes' if 'confidence' in answer.lower() else 'No'}

Note: Full critique requires LLM integration."""
