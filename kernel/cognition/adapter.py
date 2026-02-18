"""
PHASE 6: ADAPT

Determines corrective actions when monitoring detects issues.
Generates feedback and guidance for the Planner to create a better plan.
"""

from __future__ import annotations

from typing import Any

from kernel.cognition.base import BasePhase, CycleContext


class Adapter(BasePhase):
    """
    Adaptation Phase: Course correction.
    """

    async def run(self, monitor_result: Any) -> str:
        """
        Analyze monitor result and generate feedback for replanning.
        Returns a feedback string to be passed to the Planner.
        """
        if monitor_result.decision != "replan":
            return ""

        # Construct detailed feedback
        feedback_parts = [
            "Previous execution failed or drifted.",
            f"Monitor Decision: {monitor_result.decision}",
            f"Monitor Reasoning: {monitor_result.reasoning}",
        ]
        
        if hasattr(monitor_result, "gaps") and monitor_result.gaps:
            feedback_parts.append(f"identified Gaps: {monitor_result.gaps}")
             
        if hasattr(monitor_result, "drift_description") and monitor_result.drift_description:
            feedback_parts.append(f"Drift: {monitor_result.drift_description}")

        # Summarize tools errors if any
        error_count = 0
        for tool_res in self.context.tool_results:
            if tool_res.get("status") == "failed" or tool_res.get("error"):
                error_count += 1
                feedback_parts.append(f"Tool Error ({tool_res.get('tool')}): {tool_res.get('error')}")
        
        if error_count > 0:
            feedback_parts.append(f"Total Tool Errors: {error_count}. Please avoid repeating these errors.")

        # Drive: Initiative (Phase 5)
        # Use simple string matching for now since we don't have full objects
        if hasattr(monitor_result, "curiosity_questions") and monitor_result.curiosity_questions:
            feedback_parts.append("\n[INITIATIVE SUGGESTIONS]")
            for q in monitor_result.curiosity_questions[:2]:
                feedback_parts.append(f"- Proactive: Investigate '{q}'")

        return "\n".join(feedback_parts)
