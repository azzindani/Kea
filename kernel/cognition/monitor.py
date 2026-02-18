"""
PHASE 5: MONITOR (also known as KEEPER)

The agent reviews its progress:
- Are we on track?
- Is the quality sufficient?
- Are there any contradictions?
- Should we stop or pivot?
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from kernel.cognition.base import BasePhase, CycleContext
from shared.prompts import get_agent_prompt


class MonitorResult(BaseModel):
    """Output of the MONITOR phase."""
    
    on_track: bool = Field(default=True)
    drift_detected: bool = Field(default=False)
    drift_description: str = Field(default="")
    confidence: float = Field(default=0.0)
    decision: str = Field(description="continue | replan | synthesize")
    gaps: list[str] = Field(default_factory=list)
    reasoning: str = Field(default="")
    curiosity_questions: list[str] = Field(default_factory=list)


class Monitor(BasePhase):
    """
    Monitoring Phase: Self-checking progress and quality.
    Enhanced with Curiosity Drive.
    """

    async def run(self) -> MonitorResult:
        """Execute monitoring logic."""
        
        # System Prompt
        sys_prompt = get_agent_prompt("keeper_kernel")
        
        # User Prompt
        # Summarize recent execution
        summary = self._summarize_execution()
        
        user_prompt = (
            f"Review current progress.\n"
            f"Task: {self.context.task_text}\n"
            f"Recent Actions: {summary}\n"
            f"Current Facts: {self.context.memory.fact_count}\n\n"
            f"Respond in JSON with keys: on_track, drift_detected, drift_description, "
            f"confidence, decision, gaps, reasoning"
        )

        # Call LLM (Keeper)
        response = await self.context.llm_call(sys_prompt, user_prompt)
        
        result = None
        try:
            result = MonitorResult.model_validate_json(response)
        except Exception as e:
            self.logger.warning(f"Monitor parsing failed: {e}")
            result = MonitorResult(
                on_track=True,
                decision="continue",
                reasoning="Parsing failed, assuming safe to continue."
            )
            
        # ── Drive System (Phase 5): Curiosity → Attention → Initiative ──
        try:
            from kernel.drive.curiosity import get_curiosity_engine, Fact
            from kernel.drive.attention import get_attention_mechanism
            from kernel.drive.initiative import get_initiative_system

            engine = get_curiosity_engine()
            attention = get_attention_mechanism()
            initiative = get_initiative_system()

            # Convert memory facts to Fact objects
            facts = []
            raw_facts = self.context.memory.all_facts  # WorkingMemory.all_facts is a dict property
            if isinstance(raw_facts, dict):
                for k, v in raw_facts.items():
                    facts.append(Fact(entity="context", attribute=k, value=str(v)))

            # 1. Curiosity: generate exploratory questions
            questions = engine.generate_questions(facts)

            # 2. Attention: rank questions by relevance to the current task
            question_texts = [q.text for q in questions]
            if question_texts:
                focused_texts = await attention.focus(
                    query=self.context.task_text,
                    items=question_texts,
                    top_k=3,
                )
                # Re-map focused texts back to CuriosityQuestion objects
                focused_set = set(focused_texts)
                questions = [q for q in questions if q.text in focused_set]

            # 3. Initiative: convert high-priority questions into proactive suggestions
            suggestions = initiative.suggest_from_curiosity(
                questions=questions,
                budget_remaining=len(self.context.tool_results) * 100,  # proxy
            )

            # Attach top curiosity questions to result
            result.curiosity_questions = [q.text for q in questions[:3]]

            # Attach initiative suggestions as additional gaps
            for s in suggestions[:2]:
                if s.description not in result.gaps:
                    result.gaps.append(f"[INITIATIVE] {s.description}")

        except Exception as e:
            self.logger.warning(f"Drive system error: {e}")

        # Guardrails: Circular Reasoning (Phase 7)
        from kernel.logic.guardrails import detect_circular_reasoning
        if detect_circular_reasoning(self.context.tool_results):
            self.logger.warning("Guardrail: Circular logic detected! Forcing drift detection.")
            result.drift_detected = True
            result.drift_description = "Agent is executing identical tool calls repeatedly (Circular Logic)."
            result.decision = "replan"
            result.reasoning = "Detected circular loop in tool execution."
            
        return result

    def _summarize_execution(self) -> str:
        """Summarize recent tool outputs."""
        if not self.context.tool_results:
            return "No recent actions."
            
        summary = []
        for res in self.context.tool_results[-5:]: # Last 5
            summary.append(f"- Tool: {res.get('tool')} -> Output: {str(res.get('output'))[:100]}...")
        return "\n".join(summary)
