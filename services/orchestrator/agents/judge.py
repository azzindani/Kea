"""
Judge Agent.

The Synthesizer - makes final decisions based on Generator and Critic.
"""

from __future__ import annotations

from typing import Any

from shared.llm import LLMConfig, OpenRouterProvider
from shared.llm.provider import LLMMessage, LLMRole
from shared.logging import get_logger
from shared.prompts import get_agent_prompt

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
        self.system_prompt = get_agent_prompt("judge")

    async def _get_knowledge_context(self, query: str) -> str:
        """Retrieve domain-specific knowledge for judgment."""
        try:
            import asyncio

            from shared.knowledge.retriever import get_knowledge_retriever

            retriever = get_knowledge_retriever()
            context = await asyncio.wait_for(
                retriever.retrieve_skills(query, limit=2),
                timeout=3.0,
            )
            return context
        except Exception:
            return ""

    async def judge(
        self,
        query: str,
        generator_output: str,
        critic_feedback: str,
        facts: list[dict] | None = None,
    ) -> dict[str, Any]:
        """
        Judge between Generator and Critic.

        Args:
            query: Original research question
            generator_output: The Generator's answer
            critic_feedback: The Critic's critique
            facts: Optional list of facts for quality-based confidence calculation

        Returns:
            Dict with verdict, final_answer, confidence
        """
        logger.info("Judge: Evaluating arguments")

        # Calculate fact-based confidence (default if facts provided)
        # CRITICAL: If NO facts collected, confidence should be 0% (not 70%!)
        fact_based_confidence = self._calculate_fact_quality(facts) if facts else 0.0

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

            # Retrieve domain knowledge for informed judgment
            knowledge_context = await self._get_knowledge_context(query)
            system_prompt = self.system_prompt
            if knowledge_context:
                system_prompt += f"\n\n{knowledge_context}"
                logger.info(
                    f"Judge: Injecting {len(knowledge_context)} chars of domain knowledge into system prompt"
                )
            else:
                logger.debug("Judge: No domain knowledge retrieved — using base system prompt")

            messages = [
                LLMMessage(role=LLMRole.SYSTEM, content=system_prompt),
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
4. CONFIDENCE: [0.0-1.0]""",
                ),
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

            # Extract confidence if specified by LLM
            import re

            conf_match = re.search(r"confidence[:\s]+(\d+\.?\d*)", content.lower())
            if conf_match:
                try:
                    llm_confidence = float(conf_match.group(1))
                    if llm_confidence > 1:
                        llm_confidence = llm_confidence / 100
                    confidence = llm_confidence
                except ValueError:
                    pass

            # Override with fact-based confidence if available and more accurate
            # This prevents false confidence when all facts are errors or no facts exist
            if fact_based_confidence is not None:
                if fact_based_confidence == 0.0:
                    # NO facts or ALL facts are errors → confidence must be 0%
                    confidence = 0.0
                    logger.warning(
                        f"Judge: No valid facts collected! Setting confidence to 0% "
                        f"(was LLM: {confidence:.2f})"
                    )
                else:
                    # Blend LLM confidence with fact quality (70% fact, 30% LLM)
                    confidence = fact_based_confidence * 0.7 + confidence * 0.3
                    logger.info(
                        f"Judge: Blended confidence {confidence:.2f} "
                        f"(fact quality: {fact_based_confidence:.2f}, LLM: {confidence * 0.3 / 0.7:.2f})"
                    )

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

    def _calculate_fact_quality(self, facts: list[dict] | None) -> float | None:
        """
        Calculate confidence based on fact quality using embedding-based semantic analysis.

        Analyzes facts to determine how many are errors vs valid data using embeddings.
        More accurate than keyword matching - detects semantic similarity to error patterns.

        Args:
            facts: List of fact dicts with "text" field

        Returns:
            Confidence score 0.0-1.0, or None if facts unavailable
        """
        if not facts:
            return None

        total_facts = len(facts)
        if total_facts == 0:
            return None

        # Try embedding-based scoring (more accurate)
        try:
            import asyncio

            import numpy as np

            from shared.embedding.qwen3_embedding import create_embedding_provider

            embedder = create_embedding_provider(use_local=True)

            # Error pattern templates for semantic matching
            error_patterns = [
                "The tool failed to execute successfully",
                "An error occurred during execution",
                "Unable to retrieve the requested data",
                "The operation could not be completed",
                "No results were found",
                "The resource is unavailable",
                "Invalid parameters provided",
                "Exception raised during processing",
            ]

            # Valid data patterns for contrast
            valid_patterns = [
                "Successfully retrieved financial data",
                "The analysis shows positive results",
                "Data was found and processed",
                "Here are the requested metrics",
                "The information is available",
            ]

            # Get embeddings for patterns
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No loop running, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Embed patterns once
            error_embeds = loop.run_until_complete(embedder.embed(error_patterns))
            valid_embeds = loop.run_until_complete(embedder.embed(valid_patterns))

            # Calculate average pattern embeddings
            error_centroid = np.mean(error_embeds, axis=0)
            valid_centroid = np.mean(valid_embeds, axis=0)

            # Embed facts
            fact_texts = []
            for fact in facts:
                if isinstance(fact, dict):
                    fact_texts.append(str(fact.get("text", ""))[:500])  # Truncate for speed
                else:
                    fact_texts.append(str(fact)[:500])

            fact_embeds = loop.run_until_complete(embedder.embed(fact_texts))

            # Score each fact by semantic similarity
            error_count = 0
            for fact_embed in fact_embeds:
                # Cosine similarity to error vs valid patterns
                error_sim = np.dot(fact_embed, error_centroid) / (
                    np.linalg.norm(fact_embed) * np.linalg.norm(error_centroid)
                )
                valid_sim = np.dot(fact_embed, valid_centroid) / (
                    np.linalg.norm(fact_embed) * np.linalg.norm(valid_centroid)
                )

                # If more similar to error patterns, count as error
                if error_sim > valid_sim:
                    error_count += 1

            # Calculate quality score
            valid_facts = total_facts - error_count
            quality_score = valid_facts / total_facts

            # Apply penalties for high error rates
            # 0% errors = 1.0 confidence
            # 50% errors = 0.4 confidence
            # 100% errors = 0.1 confidence
            confidence = max(0.1, quality_score * 0.9 + 0.1)

            logger.info(
                f"Fact quality (embedding-based): {valid_facts}/{total_facts} valid "
                f"({error_count} errors) → confidence {confidence:.2f}"
            )

            return confidence

        except Exception as e:
            logger.warning(
                f"Embedding-based scoring failed ({e}), falling back to keyword matching"
            )

            # Fallback: keyword-based scoring
            error_count = 0
            error_indicators = [
                "failed",
                "error",
                "exception",
                "unable to",
                "could not",
                "cannot",
                "not found",
                "unavailable",
                "tool reported an error",
            ]

            for fact in facts:
                fact_text = ""
                if isinstance(fact, dict):
                    fact_text = str(fact.get("text", ""))
                else:
                    fact_text = str(fact)

                fact_lower = fact_text.lower()

                # Check if this fact is an error
                is_error = any(indicator in fact_lower for indicator in error_indicators)
                if is_error:
                    error_count += 1

            # Calculate quality score
            valid_facts = total_facts - error_count
            quality_score = valid_facts / total_facts

            # Apply penalties for high error rates
            confidence = max(0.1, quality_score * 0.9 + 0.1)

            logger.info(
                f"Fact quality (keyword-based): {valid_facts}/{total_facts} valid "
                f"({error_count} errors) → confidence {confidence:.2f}"
            )

            return confidence
