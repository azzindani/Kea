"""
Consensus Engine.

Manages the Generator/Critic/Judge adversarial collaboration loop.
"""

from __future__ import annotations

from typing import Any
from shared.logging import get_logger
from kernel.agents.generator import GeneratorAgent
from kernel.agents.critic import CriticAgent
from kernel.agents.judge import JudgeAgent
from kernel.logic.signal_bus import emit_signal, SignalType

logger = get_logger(__name__)


class ConsensusEngine:
    """
    Orchestrates adversarial collaboration between agents.
    
    Flow:
    1. Generator creates initial answer
    2. Critic critiques the answer
    3. Judge makes final determination
    4. Optionally loop for refinement
    """
    
    def __init__(self, max_rounds: int = 32768):
        self.generator = GeneratorAgent()
        self.critic = CriticAgent()
        self.judge = JudgeAgent()
        self.max_rounds = max_rounds
    
    async def reach_consensus(
        self,
        query: str,
        facts: list,
        sources: list,
    ) -> dict[str, Any]:
        """
        Run the consensus loop until agreement or max rounds.
        
        Args:
            query: Research question
            facts: Collected facts
            sources: Source references
            
        Returns:
            Dict with final_answer, confidence, rounds, history
        """
        logger.info(f"Consensus: Starting with {len(facts)} facts")
        
        history = []
        current_answer = ""
        
        for round_num in range(self.max_rounds):
            logger.info(f"Consensus: Round {round_num + 1}/{self.max_rounds}")
            
            # Generator phase
            if round_num == 0:
                generator_output = await self.generator.generate(query, facts, sources)
            else:
                # Incorporate previous feedback
                generator_output = await self.generator.generate(
                    f"{query}\n\nPrevious feedback: {history[-1].get('critique', '')}",
                    facts,
                    sources
                )
            
            current_answer = generator_output
            
            # Critic phase
            critic_feedback = await self.critic.critique(generator_output, facts, sources)
            
            # Judge phase
            judgment = await self.judge.judge(query, generator_output, critic_feedback, facts=facts)
            
            # Record history
            history.append({
                "round": round_num + 1,
                "generator": generator_output[:500],
                "critique": critic_feedback[:500],
                "verdict": judgment["verdict"],
                "confidence": judgment["confidence"],
            })
            
            # Adaptive threshold: degrade by 0.05 per round (0.95   0.90   0.85...)
            adaptive_threshold = max(0.95 - (round_num * 0.05), 0.60)
            
            # DELTA CHECK: How much did confidence change?
            last_conf = history[-2]["confidence"] if len(history) > 1 else 0.0
            delta = abs(judgment["confidence"] - last_conf)
            
            # Emit Signal
            emit_signal(
                SignalType.CONVERGENCE,
                "ConsensusEngine",
                judgment["verdict"].upper(),
                judgment["confidence"],
                round=round_num + 1,
                delta=delta,
                threshold=adaptive_threshold
            )
            
            # Check if we can stop early with adaptive threshold
            if judgment["verdict"] == "Accept" and judgment["confidence"] >= adaptive_threshold:
                logger.info(f"Consensus: Accepted (conf {judgment['confidence']:.2f} >= threshold {adaptive_threshold:.2f}) in round {round_num + 1}")
                break
            
            # Allow early exit if confidence is plateauing high (diminishing returns)
            if round_num >= 2 and delta < 0.02 and judgment["confidence"] > 0.8:
                logger.info(f"Consensus: Convergence plateau (delta {delta:.3f} < 0.02) at high confidence. Stopping.")
                break
            
            if judgment["verdict"] == "Reject" and round_num >= 4: # Increased max strict rounds
                logger.info("Consensus: Max strict rounds reached. Continuing with best effort.")
                break
        
        # Final result
        final_confidence = history[-1]["confidence"] if history else 0.5
        
        return {
            "final_answer": judgment.get("final_answer", current_answer),
            "confidence": final_confidence,
            "rounds": len(history),
            "final_verdict": history[-1]["verdict"] if history else "Unknown",
            "history": history,
        }


async def consensus_node(state: dict[str, Any]) -> dict[str, Any]:
    """LangGraph node for consensus."""
    engine = ConsensusEngine(max_rounds=2)
    
    result = await engine.reach_consensus(
        query=state.get("query", ""),
        facts=state.get("facts", []),
        sources=state.get("sources", []),
    )
    
    state["generator_output"] = result["final_answer"]
    state["confidence"] = result["confidence"]
    state["consensus_rounds"] = result["rounds"]
    state["consensus_history"] = result["history"]
    
    logger.info(f"Consensus: Completed in {result['rounds']} rounds")
    return state
