"""
PHASE 7: PACKAGE

The agent synthesizes all gathered information into the final deliverable.
- Formats: Markdown report, JSON data, structured object
- Validation: Ensures all required fields are present
- Attribution: Cites sources
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from kernel.cognition.base import BasePhase, CycleContext
from kernel.io.output_schemas import WorkPackage
from shared.prompts import get_agent_prompt


class Packager(BasePhase):
    """
    Packaging Phase: Creating the final deliverable.
    """

    async def run(self, perception: Any, framing: Any, **kwargs) -> WorkPackage:
        """Execute packaging logic."""
        
        # System Prompt
        sys_prompt = get_agent_prompt("kernel_packager")
        
        # User Prompt
        # Gather all artifacts and memory
        facts_dict = self.context.memory.all_facts  # dict[str, str]
        facts_text = "\n".join(f"- {k}: {v}" for k, v in list(facts_dict.items())[:15])
        
        user_prompt = (
            f"Package the findings into a final response.\n"
            f"Original Task: {self.context.task_text}\n"
            f"Perceived Intent: {perception.task_text}\n"
            f"Framing: {framing.restatement}\n"
            f"Facts Gathered:\n{facts_text}\n\n"
            f"Create a comprehensive WorkPackage JSON with: "
            f"summary, detailed_content, sources, confidence_score (0.0-1.0), "
            f"data_gaps, artifacts (if any)."
        )

        # Call LLM
        # We enforce WorkPackage schema via KEI
        response = await self.context.llm_call(sys_prompt, user_prompt)
        
        try:
            # The KEI engine might return the object directly if structured_complete was used
            # But here we are simulating raw call + parse.
            # In real KEI, we'd pass response_model=WorkPackage.
            # Let's assume the wrapper handles it or we parse JSON.
            from shared.utils.parsing import parse_llm_json
            return parse_llm_json(response, WorkPackage)
        except Exception as e:
            self.logger.warning(f"Packaging parsing failed: {e}")
            return WorkPackage(
                summary="Packaging failed.",
                detailed_content=self.context.task_text,
                sources=[],
                confidence_score=0.0
            )
