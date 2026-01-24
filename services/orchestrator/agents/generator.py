"""
Generator Agent.

The Optimist - generates comprehensive answers from facts.
"""

from __future__ import annotations

from typing import Any
from shared.logging import get_logger
from shared.llm import OpenRouterProvider, LLMConfig
from shared.llm.provider import LLMMessage, LLMRole

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
        self.system_prompt = """You are the Generator - an optimistic research assistant.

Your role:
- Synthesize facts into comprehensive answers
- Find connections between disparate information
- Present findings in a clear, structured manner
- Be thorough but not verbose

CRITICAL ANTI-HALLUCINATION RULES:
1. ONLY use information from the provided "Available Facts"
2. NEVER invent, fabricate, or guess any data (numbers, dates, names, statistics)
3. If asked about something not in the facts, say "This data was not collected"
4. If a task failed or wasn't executed, acknowledge it - don't make up results
5. Always cite which facts support your claims
6. When in doubt, say "Information not available" rather than guessing

Always cite your sources when making claims."""
    
    async def generate(self, query: str, facts: list, sources: list) -> str:
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
            config = LLMConfig(
                model="nvidia/nemotron-3-nano-30b-a3b:free",
                temperature=0.6,
                max_tokens=800,
            )
            
            facts_text = "\n".join([
                f"- {f.get('text', str(f)) if isinstance(f, dict) else str(f)}"
                for f in facts[:15]
            ]) if facts else "No facts available"
            
            messages = [
                LLMMessage(role=LLMRole.SYSTEM, content=self.system_prompt),
                LLMMessage(
                    role=LLMRole.USER,
                    content=f"""Research Question: {query}

Available Facts:
{facts_text}

Generate a comprehensive answer that:
1. Directly addresses the question
2. Uses the available facts
3. Identifies any gaps in information
4. Provides a confidence assessment"""
                )
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

{chr(10).join([f'- {str(f)[:100]}' for f in facts[:5]])}

Note: Full generation requires LLM integration."""
