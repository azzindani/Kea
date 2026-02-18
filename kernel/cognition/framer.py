"""
PHASE 2: FRAME (also known as EXPLORE/FRAME)

After perceiving the raw request, the agent explores potential tools and then frames the problem.
- Restatement: "The user actually wants X, Y, and Z."
- Assumptions: "This implies we need live data for X."
- Constraints: "Budget is tight, prioritize free sources."
- Knowledge Gaps: "I don't know the current CEO of Company A."
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from kernel.cognition.base import BasePhase, CycleContext
from shared.prompts import get_agent_prompt


class FramingResult(BaseModel):
    """Output of the FRAME phase."""

    restatement: str = Field(description="Problem restated in own words")
    assumptions: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    known_facts: list[str] = Field(
        default_factory=list,
        description="Facts already known (from memory/context)",
    )
    unknown_gaps: list[str] = Field(
        default_factory=list,
        description="Information gaps that need to be filled",
    )


class Framer(BasePhase):
    """
    Framing Phase: Setting boundaries and identifying gaps.
    """

    async def run(self, perception: Any) -> FramingResult:
        """Execute framing logic."""
        
        # Tool context
        tool_desc = self._format_tools()
        
        # System Prompt
        sys_prompt = get_agent_prompt("kernel_framer")
        
        # User Prompt
        task = self.context.task_text
        perc_text = perception.task_text
        context_str = f"Tools: {tool_desc}"

        user_prompt = (
            f"Frame this problem.\n"
            f"Original Task: {task}\n"
            f"Perceived Intent: {perc_text}\n"
            f"Context: {context_str}\n\n"
            f"Respond in JSON format with keys: restatement, assumptions, constraints, "
            f"scope_boundaries, known_facts, unknown_gaps"
        )

        # Call LLM
        response = await self.context.llm_call(sys_prompt, user_prompt)
        
        try:
            result = FramingResult.model_validate_json(response)
            return result
        except Exception as e:
            self.logger.warning(f"Framing parsing failed: {e}")
            return FramingResult(
                restatement=self.context.task_text,
                assumptions=["Parsing failed"],
                unknown_gaps=[]
            )

    def _format_tools(self) -> str:
        """Format available tools for prompt."""
        if not self.context.available_tools:
            return "No specialized tools available beyond standard reasoning."
            
        lines = []
        for t in self.context.available_tools:
            lines.append(f"- {t.get('name')}: {t.get('description')}")
        return "\n".join(lines)
