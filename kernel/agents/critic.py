"""
Critic Agent.

The Pessimist - challenges assumptions and finds weaknesses.
"""

from __future__ import annotations

from shared.llm import LLMConfig, OpenRouterProvider
from shared.llm.provider import LLMMessage, LLMRole
from shared.logging import get_logger
from shared.prompts import get_agent_prompt
from shared.embedding.model_manager import get_embedding_provider
from kernel.logic.signal_bus import emit_signal, SignalType

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
        self.system_prompt = get_agent_prompt("critic")
        self._embedding_provider = None

    async def _get_provider(self):
        if self._embedding_provider is None:
            self._embedding_provider = get_embedding_provider()
        return self._embedding_provider

    async def _measure_alignment(self, answer: str, facts: list[Any]) -> float:
        """Measure semantic alignment between answer and facts."""
        try:
            if not facts:
                return 0.5
            
            provider = await self._get_provider()
            
            # Embed answer
            answer_emb = await provider.embed_query(answer[:1000]) # Truncate for speed
            
            # Embed facts (batch)
            fact_texts = []
            for f in facts[:10]: # Top 10 facts
                if isinstance(f, dict):
                    # Try common fact keys
                    text = f.get("text") or f.get("content") or f.get("value") or str(f)
                    fact_texts.append(str(text)[:500])
                else:
                    fact_texts.append(str(f)[:500])
            
            if not fact_texts:
                return 0.5
                
            fact_embs = await provider.embed(fact_texts)
            
            # Find max alignment (support)
            max_sim = 0.0
            for f_emb in fact_embs:
                dot = sum(a * b for a, b in zip(answer_emb, f_emb))
                max_sim = max(max_sim, dot)
                
            return max_sim
        except Exception as e:
            logger.warning(f"Critic alignment check failed: {e}")
            return 0.0

    async def _get_knowledge_context(self, query: str) -> str:
        """Retrieve domain-specific rules and knowledge for critique."""
        try:
            import asyncio

            from shared.knowledge.retriever import get_knowledge_retriever

            retriever = get_knowledge_retriever()
            context = await asyncio.wait_for(
                retriever.retrieve_all(query, skill_limit=1, rule_limit=2),
                timeout=3.0,
            )
            return context
        except Exception:
            return ""

    async def critique(
        self,
        answer: str,
        facts: list,
        sources: list,
        query: str = "",
        knowledge_context: str | None = None,
    ) -> str:
        """
        Critique a generated answer.

        Args:
            answer: The Generator's answer
            facts: Available facts
            sources: Source references
            query: Original research query (for knowledge retrieval)
            knowledge_context: Optional pre-retrieved knowledge context

        Returns:
            Critique with specific feedback
        """
        logger.info("Critic: Analyzing answer")

        try:
            import os

            if not os.getenv("OPENROUTER_API_KEY"):
                return self._fallback_critique(answer)

            provider = OpenRouterProvider()
            from shared.config import get_settings

            config = LLMConfig(
                model=get_settings().models.critic_model,
                temperature=0.4,
                max_tokens=32768,
            )

            # Retrieve domain knowledge (especially rules) for informed critique if not provided
            if knowledge_context is None:
                knowledge_context = await self._get_knowledge_context(query or answer[:200])
                
            system_prompt = self.system_prompt
            if knowledge_context:
                system_prompt += f"\n\n{knowledge_context}"
                logger.info(
                    f"Critic: Injecting {len(knowledge_context)} chars of domain knowledge into system prompt"
                )
            else:
                logger.debug("Critic: No domain knowledge retrieved — using base system prompt")

            from shared.vocab import load_vocab
            vocab = load_vocab("critic")
            prompt_template = vocab.get("prompt", "Critique this answer: {answer}")

            messages = [
                LLMMessage(role=LLMRole.SYSTEM, content=system_prompt),
                LLMMessage(
                    role=LLMRole.USER,
                    content=prompt_template.format(
                        answer=answer[:1500],
                        fact_count=len(facts),
                        source_count=len(sources),
                    ),
                ),
            ]

            response = await provider.complete(messages, config)

            # Measure fact alignment (HALLUCINATION CHECK)
            alignment_score = await self._measure_alignment(answer, facts)
            logger.info(f"Critic: Fact alignment score = {alignment_score:.2f}")

            # Emit Adversarial Signal
            emit_signal(
                SignalType.ADVERSARIAL,
                "CriticAgent",
                "CRITIQUE_GENERATED",
                confidence=0.9, # Confidence in the critique itself
                alignment_score=alignment_score,
                critique_length=len(response.content),
                has_citations="source" in response.content.lower()
            )

            logger.info(f"Critic: Critique complete ({len(response.content)} chars):\n{response.content[:2000]}")
            return response.content

        except Exception as e:
            logger.error(f"Critic error: {e}")
            return self._fallback_critique(answer)

    def _fallback_critique(self, answer: str) -> str:
        """Fallback critique without LLM."""
        from shared.vocab import load_vocab
        vocab = load_vocab("critic")
        fallback_template = vocab.get("fallback", "Critique length: {length}")
        
        return fallback_template.format(
            length=len(answer),
            citations="Present" if "source" in answer.lower() else "Missing",
            confidence="Yes" if "confidence" in answer.lower() else "No",
        )
