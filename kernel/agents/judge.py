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
        knowledge_context: str | None = None,
    ) -> dict[str, Any]:
        """
        Judge between Generator and Critic.

        Args:
            query: Original research question
            generator_output: The Generator's answer
            critic_feedback: The Critic's critique
            facts: Optional list of facts for quality-based confidence calculation
            knowledge_context: Optional pre-retrieved knowledge context

        Returns:
            Dict with verdict, final_answer, confidence
        """
        logger.info("Judge: Evaluating arguments")

        # Calculate fact-based confidence (default if facts provided)
        # CRITICAL: If NO facts collected, confidence should be 0% (not 70%!)
        fact_based_confidence = await self._calculate_fact_quality(facts) if facts else 0.0

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

            # Retrieve domain knowledge for informed judgment if not provided
            if knowledge_context is None:
                knowledge_context = await self._get_knowledge_context(query)
                
            system_prompt = self.system_prompt
            if knowledge_context:
                system_prompt += f"\n\n{knowledge_context}"
                logger.info(
                    f"Judge: Injecting {len(knowledge_context)} chars of domain knowledge into system prompt"
                )
            else:
                logger.debug("Judge: No domain knowledge retrieved — using base system prompt")

            from shared.vocab import load_vocab
            vocab = load_vocab("judgment")
            prompt_template = vocab.get("prompts", {}).get("user_request", "{query}")

            messages = [
                LLMMessage(role=LLMRole.SYSTEM, content=system_prompt),
                LLMMessage(
                    role=LLMRole.USER,
                    content=prompt_template.format(
                        query=query,
                        generator_output=generator_output[:1000],
                        critic_feedback=critic_feedback[:800],
                    ),
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
                    # NO facts or ALL facts are errors — confidence must be 0%
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
            logger.info(f"Judge Reasoning: {content[:2000]}")

            # v0.4.1 Fix: final_answer should be the generator output if accepted/revised,
            # NOT the judge's reasoning string, unless it's a rejection/error.
            final_ans = generator_output
            if verdict == "Reject":
                final_ans = f"REJECTED: {content}"

            return {
                "verdict": verdict,
                "reasoning": content,
                "final_answer": final_ans,
                "confidence": confidence,
            }

        except Exception as e:
            logger.error(f"Judge error: {e}")
            return self._fallback_judge(generator_output, critic_feedback)

    def _fallback_judge(self, generator_output: str, critic_feedback: str) -> dict:
        """Fallback judgment without LLM."""
        from shared.vocab import load_vocab
        vocab = load_vocab("judgment")
        f_vars = vocab.get("fallbacks", {})
        
        return {
            "verdict": f_vars.get("verdict", "Accept"),
            "reasoning": f_vars.get("reasoning", "Fallback: Accepting generator output."),
            "final_answer": generator_output,
            "confidence": f_vars.get("confidence", 0.5),
        }

    async def _calculate_fact_quality(self, facts: list[dict] | None) -> float | None:
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
            import numpy as np

            from shared.embedding.model_manager import get_embedding_provider

            embedder = get_embedding_provider()

            from shared.vocab import load_vocab
            
            vocab = load_vocab("judgment")
            scoring_patterns = vocab.get("scoring", {})

            # Error pattern templates for semantic matching
            error_patterns = scoring_patterns.get("error", [
                "The tool failed to execute successfully",
                "An error occurred during execution"
            ])

            # Low-information patterns (Reward Shaping: penalize "I don't know" answers)
            low_info_patterns = scoring_patterns.get("low_info", [
                "Information is not available",
                "Data could not be verified"
            ])

            # High-reward patterns (Substantive Data)
            valid_patterns = scoring_patterns.get("valid", [
                "Revenue increased by 15%",
                "Net income was $500 million"
            ])

            # Embed patterns
            error_embeds = await embedder.embed(error_patterns)
            low_info_embeds = await embedder.embed(low_info_patterns)
            valid_embeds = await embedder.embed(valid_patterns)
            
            error_centroid = np.mean(error_embeds, axis=0)
            low_info_centroid = np.mean(low_info_embeds, axis=0)
            valid_centroid = np.mean(valid_embeds, axis=0)

            # Embed facts
            fact_texts = []
            for fact in facts:
                if isinstance(fact, dict):
                    # Combine key and value for better context
                    k = fact.get("key", "") or fact.get("entity", "")
                    v = str(fact.get("content", "") or fact.get("value", "") or fact.get("text", ""))[:500]
                    fact_texts.append(f"{k}: {v}")
                else:
                    fact_texts.append(str(fact)[:500])

            if not fact_texts:
                return 0.0

            fact_embeds = await embedder.embed(fact_texts)

            # Score each fact by semantic similarity
            score_sum = 0.0
            
            for fact_embed in fact_embeds:
                norm_fact = np.linalg.norm(fact_embed)
                
                # Cosine similarities
                sim_error = np.dot(fact_embed, error_centroid) / (norm_fact * np.linalg.norm(error_centroid))
                sim_low_info = np.dot(fact_embed, low_info_centroid) / (norm_fact * np.linalg.norm(low_info_centroid))
                sim_valid = np.dot(fact_embed, valid_centroid) / (norm_fact * np.linalg.norm(valid_centroid))

                # Reward Function:
                # +1.0 for Signal (Valid > others)
                # 0.0 for Noise (Low Info > others)
                # -1.0 for Errors (Error > others)
                
                if sim_error > sim_valid and sim_error > sim_low_info:
                    # It's an error
                    score_sum -= 1.0
                elif sim_low_info > sim_valid and sim_low_info > sim_error:
                    # It's low info / empty calorie fact
                    score_sum += 0.2  # Slight credit for admitting ignorance, but mostly useless
                else:
                    # It's valid content
                    score_sum += 1.0

            # Normalize to 0.0 - 1.0 range based on potential max score
            # Max possible = len(facts) * 1.0
            # Min possible = len(facts) * -1.0
            # We want to map this to a confidence probability.
            
            avg_score = score_sum / total_facts
            # avg_score is roughly between -1.0 and 1.0
            
            # Sigmoid-like mapping:
            # 1.0 -> 0.95
            # 0.5 -> 0.8
            # 0.0 -> 0.4 (neutral/mixed)
            # -0.5 -> 0.2
            # -1.0 -> 0.05
            
            confidence = max(0.0, min(1.0, (avg_score + 1) / 2))
            
            # Heuristic penalty: if we have very few facts, confidence ceiling
            if total_facts < 3:
                confidence = min(confidence, 0.6)

            logger.info(
                f"Fact Quality Reward: avg_score={avg_score:.2f} -> confidence={confidence:.2f} (facts={total_facts})"
            )

            return confidence

        except Exception as e:
            logger.warning(
                f"Embedding-based scoring failed ({e}), falling back to keyword matching"
            )

            # Fallback: keyword-based scoring
            vocab = load_vocab("judgment")
            keywords = vocab.get("keywords", {})
            
            error_count = 0
            low_info_count = 0
            
            error_indicators = keywords.get("error", [])
            low_info_indicators = keywords.get("low_info", [])

            if not error_indicators:
                 # Default fallback if vocab fails
                 error_indicators = ["failed", "error", "exception", "unable to", "not found"]
            
            if not low_info_indicators:
                 low_info_indicators = ["unknown", "not provided", "no data", "missing"]

            for fact in facts:
                fact_text = ""
                if isinstance(fact, dict):
                    fact_text = str(fact.get("text", "") or fact.get("value", ""))
                else:
                    fact_text = str(fact)

                fact_lower = fact_text.lower()

                if any(x in fact_lower for x in error_indicators):
                    error_count += 1
                elif any(x in fact_lower for x in low_info_indicators):
                    low_info_count += 1

            # Simple linear score
            # Error = -1, LowInfo = 0.2, Good = 1.0
            good_count = total_facts - error_count - low_info_count
            score = (good_count * 1.0 + low_info_count * 0.2 - error_count * 1.0)
            avg_score = score / total_facts if total_facts > 0 else 0
            
            confidence = max(0.0, min(1.0, (avg_score + 1) / 2))
            
            logger.info(
                f"Fact Quality (Keyword): Good={good_count} LowInfo={low_info_count} Err={error_count} -> Conf={confidence:.2f}"
            )

            return confidence

        except Exception as e:
            logger.warning(
                f"Scoring failed ({e}), using last-resort defaults"
            )

            # Fallback: simple count
            # Calculate quality score
            valid_facts = total_facts - error_count
            quality_score = valid_facts / total_facts if total_facts > 0 else 0

            # Apply penalties for high error rates
            confidence = max(0.1, quality_score * 0.9 + 0.1)

            logger.info(
                f"Fact quality (final fallback): {valid_facts}/{total_facts} valid "
                f"({error_count} errors)   confidence {confidence:.2f}"
            )

            return confidence
