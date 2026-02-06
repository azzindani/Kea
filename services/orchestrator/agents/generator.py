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
5. ALWAYS cite source URLs for every claim
6. When in doubt, say "Information not available" rather than guessing

MANDATORY CITATION FORMAT:
- For financial data: "According to Yahoo Finance [https://finance.yahoo.com/quote/TICKER], ..."
- For web sources: "Source: [URL]"
- For internal computations: "Based on internal calculation from [tool_name]"
- NEVER make a numerical claim without a citation

EXAMPLE (CORRECT):
"BCA Bank's 2025 free cash flow was 75.06T IDR [Source: https://finance.yahoo.com/quote/BBCA.JK]"

EXAMPLE (INCORRECT - NO CITATION):
"BCA Bank's 2025 free cash flow was 75.06T IDR" ❌ MISSING SOURCE URL

Every fact, number, or claim MUST be followed by [Source: URL] immediately."""
    
    async def generate(self, query: str, facts: list, sources: list, revision_feedback: str = None) -> str:
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
            
            # Format facts with source URLs for citation
            facts_text = ""
            for idx, f in enumerate(facts):
                if isinstance(f, dict):
                    text = f.get('text', str(f))
                    source_url = f.get('source_url', 'unknown')
                    tool = f.get('source', 'unknown')
                    facts_text += f"[Fact #{idx+1}] {text}\n  Source: {source_url} (via {tool})\n\n"
                else:
                    facts_text += f"[Fact #{idx+1}] {str(f)}\n  Source: unknown\n\n"

            if not facts_text:
                facts_text = "No facts available"

            # Format sources list
            sources_text = "\n".join([
                f"- {s.get('url', 'unknown')} ({s.get('tool', 'unknown')})"
                for s in sources
            ]) if sources else "No sources available"

            # Add revision feedback if this is a revision
            revision_context = ""
            if revision_feedback:
                revision_context = f"""

⚠️ REVISION REQUESTED
The Critic identified issues with your previous answer. Address these points:

{revision_feedback}

You MUST fix these issues in your revised answer."""

            messages = [
                LLMMessage(role=LLMRole.SYSTEM, content=self.system_prompt),
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

CRITICAL: Every fact, statistic, or number MUST be followed by [Source: URL]."""
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
