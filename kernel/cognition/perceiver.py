"""
PHASE 1: PERCEIVE

The agent parses the raw instruction to understand:
- Core Intent: What is actually being asked?
- Implicit Expectations: What is not said but required?
- Key Entities: Who/what is this about?
- Knowledge Gaps: What do I need to find out?
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from kernel.cognition.base import BasePhase
from shared.prompts import get_agent_prompt


class PerceptionResult(BaseModel):
    """Output of the PERCEIVE phase."""

    task_text: str = Field(description="The core instruction")
    implicit_expectations: list[str] = Field(
        default_factory=list,
        description="Implicit requirements not stated explicitly",
    )
    key_entities: list[str] = Field(
        default_factory=list,
        description="Key entities/topics mentioned in the task",
    )
    intent_path: str = Field(
        default="D",
        description="Intent path: A (memory) | B (verify) | C (synthesis) | D (deep research)",
    )

    @field_validator("implicit_expectations", "key_entities", mode="before")
    @classmethod
    def parse_list_fields(cls, v: Any) -> list[str]:
        """Handle LLM returning a single string instead of a list."""
        if isinstance(v, str):
            if "\n" in v:
                return [line.strip("- *") for line in v.split("\n") if line.strip()]
            return [v]
        if isinstance(v, list):
            return [str(item) for item in v]
        return []


class Perceiver(BasePhase):
    """
    Perception Phase: Restating and understanding the task.
    """

    async def run(self, **kwargs) -> PerceptionResult:
        """Execute perception logic."""
        
        # System Prompt
        sys_prompt = get_agent_prompt("kernel_perceiver")
        
        # User Prompt
        task = self.context.task_text
        user_prompt = (
            f"Analyze this task. Identify:\n"
            f"1. The core instruction (what specifically is being asked)\n"
            f"2. Implicit expectations (what the requester probably expects)\n"
            f"3. Key entities/topics mentioned\n"
            f"4. Expected output format\n"
            f"5. Urgency level (normal/high/critical)\n\n"
            f"Task: {task}\n"
            f"\nRespond in JSON format with keys: task_text, implicit_expectations, key_entities, output_format_hint, urgency"
        )

        # Call LLM
        response = await self.context.llm_call(sys_prompt, user_prompt)
        
        try:
            from shared.utils.parsing import parse_llm_json
            return parse_llm_json(response, PerceptionResult)
        except Exception as e:
            self.logger.warning(f"Perception parsing failed: {e}. Fallback to raw.")
            return PerceptionResult(
                task_text=self.context.task_text,
                implicit_expectations=["Parse failed, proceed with caution"],
                intent_path="D"
            )

    def _get_memory_context(self) -> str:
        """Get relevant memory context string."""
        facts = self.context.memory.all_facts  # dict[str, str]
        if not facts:
            return "No prior context."
        items = list(facts.items())[:5]
        return "\n".join(f"- {k}: {v}" for k, v in items)
