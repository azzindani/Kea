"""
Judge Agent.

The Synthesizer - makes final decisions based on Generator and Critic.
"""

from __future__ import annotations

from typing import Any
from shared.logging import get_logger
from shared.llm import OpenRouterProvider, LLMConfig
from shared.llm.provider import LLMMessage, LLMRole

logger = get_logger(__name__)


class JudgeAgent:
    """
    The Judge (Synthesizer) Agent.
    
    Role: Evaluate Generator and Critic, make final decision.
    Personality: Balanced, fair, decisive.
    """
    
    def __init__(self):
        self.name = "Judge"
        self.role = "The Synthesizer"
        self.system_prompt = """You are the Judge - a balanced decision-maker.

Your role:
- Weigh the Generator's answer against the Critic's feedback
- Make a final determination
- Synthesize the best elements of both perspectives
- Provide a clear verdict

Be fair and explain your reasoning."""
    
    async def judge(
        self,
        query: str,
        generator_output: str,
        critic_feedback: str,
    ) -> dict[str, Any]:
        """
        Judge between Generator and Critic.
        
        Args:
            query: Original research question
            generator_output: The Generator's answer
            critic_feedback: The Critic's critique
            
        Returns:
            Dict with verdict, final_answer, confidence
        """
        logger.info("Judge: Evaluating arguments")
        
        try:
            import os
            if not os.getenv("OPENROUTER_API_KEY"):
                return self._fallback_judge(generator_output, critic_feedback)
            
            provider = OpenRouterProvider()
            from shared.config import get_settings
            config = LLMConfig(
                model=get_settings().models.critic_model,
                temperature=0.3,
                max_tokens=32768,
            )
            
            messages = [
                LLMMessage(role=LLMRole.SYSTEM, content=self.system_prompt),
                LLMMessage(
                    role=LLMRole.USER,
                    content=f"""Original Question: {query}

=== GENERATOR'S ANSWER ===
{generator_output[:1000]}

=== CRITIC'S FEEDBACK ===
{critic_feedback[:800]}

Provide:
1. VERDICT: [Accept/Revise/Reject]
2. REASONING: [Why this decision]
3. FINAL ANSWER: [Your synthesized answer incorporating valid critiques]
4. CONFIDENCE: [0.0-1.0]"""
                )
            ]
            
            response = await provider.complete(messages, config)
            
            # Parse verdict
            content = response.content
            verdict = "Accept"
            confidence = 0.7
            
            if "reject" in content.lower():
                verdict = "Reject"
                confidence = 0.3
            elif "revise" in content.lower():
                verdict = "Revise"
                confidence = 0.6
            
            # Extract confidence if specified
            import re
            conf_match = re.search(r'confidence[:\s]+(\d+\.?\d*)', content.lower())
            if conf_match:
                try:
                    confidence = float(conf_match.group(1))
                    if confidence > 1:
                        confidence = confidence / 100
                except ValueError:
                    pass
            
            logger.info(f"Judge: Verdict={verdict}, Confidence={confidence:.2f}")
            
            return {
                "verdict": verdict,
                "reasoning": content,
                "final_answer": content,
                "confidence": confidence,
            }
            
        except Exception as e:
            logger.error(f"Judge error: {e}")
            return self._fallback_judge(generator_output, critic_feedback)
    
    def _fallback_judge(self, generator_output: str, critic_feedback: str) -> dict:
        """Fallback judgment without LLM."""
        return {
            "verdict": "Accept",
            "reasoning": "Fallback: Accepting generator output without full evaluation.",
            "final_answer": generator_output,
            "confidence": 0.5,
        }
