"""
PHASE 3: PLAN

The agent generates a concrete plan of action.
- Strategy: High-level approach ("Use search, then compare")
- Steps: Specific tool calls or reasoning steps
- Contingency: "If search fails, try direct lookup."
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from kernel.cognition.base import BasePhase, CycleContext
from shared.prompts import get_agent_prompt


class PlanStep(BaseModel):
    """A single step in the plan."""
    step_id: str = Field(description="step_1, step_2, etc.")
    description: str = Field(description="What to do")
    tool: str | None = Field(default=None, description="Tool to use")
    args: dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    depends_on: list[str] = Field(default_factory=list, description="Step IDs required before this step")


class PlanResult(BaseModel):
    """Output of the PLAN phase."""

    approach: str = Field(description="High-level strategy")
    steps: list[PlanStep] = Field(description="Ordered steps to execute")
    estimated_tools: int = Field(default=0)
    risk_factors: list[str] = Field(
        default_factory=list,
        description="Potential failure modes",
    )

    @field_validator("steps", mode="before")
    @classmethod
    def parse_steps(cls, v: Any) -> list[dict[str, Any]]:
        """Handle LLM returning a list of strings instead of list of objects."""
        if not isinstance(v, list):
            return []
            
        cleaned_steps = []
        for i, item in enumerate(v):
            if isinstance(item, str):
                cleaned_steps.append({
                    "step_id": f"step_{i+1}",
                    "description": item,
                    "tool": None,
                    "args": {},
                    "depends_on": [f"step_{i}" for i in range(1, i+1)] if i > 0 else []
                })
            else:
                cleaned_steps.append(item)
        return cleaned_steps


class Planner(BasePhase):
    """
    Planning Phase: Defining the execution path.
    """

    async def run(self, perception: Any, framing: Any, feedback: str = "", **kwargs) -> PlanResult:
        """Execute planning logic."""
        
        # System Prompt
        sys_prompt = get_agent_prompt("kernel_planner")
        
        # User Prompt
        # Inject framing results into prompt
        context_str = (
            f"Framing: {framing.restatement}\n"
            f"Gaps: {framing.unknown_gaps}\n"
            f"Assumptions: {framing.assumptions}\n"
        )
        
        if feedback:
             context_str += f"\nFEEDBACK / PREVIOUS FAILURE: {feedback}\n"
        
        user_prompt = (
            f"Plan the execution for this task.\n"
            f"Task: {self.context.task_text}\n"
            f"Context:\n{context_str}\n"
            f"Tools Available:\n{self._format_tools()}\n\n"
            f"Create a step-by-step plan. For each step, specify the tool to use (if any) "
            f"and the specific arguments. Define dependencies between steps."
        )

        # Call LLM
        # We rely on KnowledgeEnhancedInference to append the JSON Schema for PlanResult
        response = await self.context.llm_call(sys_prompt, user_prompt)
        
        try:
            from shared.utils.parsing import parse_llm_json
            result = parse_llm_json(response, PlanResult)
            
            # Simple validation: ensure steps have IDs
            for i, step in enumerate(result.steps):
                if not step.step_id:
                    step.step_id = f"step_{i+1}"
                    
            return result
            
        except Exception as e:
            self.logger.warning(f"Planning parsing failed: {e}")
            # Fallback simple plan
            return PlanResult(
                approach="Direct Execution (Fallback)",
                steps=[
                    PlanStep(
                        step_id="step_1",
                        description=f"Directly address: {self.context.task_text}",
                        tool=None
                    )
                ]
            )

    def _format_tools(self) -> str:
        """Format available tools for prompt."""
        if not self.context.available_tools:
            return "No tools available."
            
        lines = []
        for t in self.context.available_tools:
            # Include args schema for planner accuracy
            args_schema = t.get("input_schema", {}).get("properties", {})
            lines.append(f"- {t.get('name')}: {t.get('description')} Args: {list(args_schema.keys())}")
        return "\n".join(lines)
