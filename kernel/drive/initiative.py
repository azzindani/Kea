"""
Initiative Drive.

Generating proactive tasks and suggestions based on internal state.
Transforms passive "wait for command" to active "suggest action".
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from kernel.drive.curiosity import CuriosityQuestion
from shared.logging import get_logger

logger = get_logger(__name__)


class InitiativeType(str, Enum):
    EXPLORE = "explore"      # Investigate a curiosity question
    CLARIFY = "clarify"      # Ask for more info on ambiguous input
    VERIFY = "verify"        # Double-check a low-confidence fact
    PIVOT = "pivot"          # Change strategy if stuck
    OPTIMIZE = "optimize"    # Improve efficiency


@dataclass
class ProactiveSuggestion:
    """A generated task suggestion."""
    type: InitiativeType
    description: str
    rationale: str
    priority: float  # 0.0 - 1.0 urgency
    context: dict[str, Any] | None = None


class InitiativeSystem:
    """
    Generates suggestions for next steps based on internal drives.
    """

    def suggest_from_curiosity(
        self,
        questions: list[CuriosityQuestion],
        budget_remaining: int,
    ) -> list[ProactiveSuggestion]:
        """
        Suggest exploration tasks from high-priority curiosity questions.
        """
        suggestions = []
        
        # Only explore if budget allows
        if budget_remaining < 1000:
            return []

        for q in questions[:3]:
            if q.priority > 0.7:
                suggestions.append(ProactiveSuggestion(
                    type=InitiativeType.EXPLORE,
                    description=f"Investigate: {q.text}",
                    rationale=f"High curiosity ({q.priority:.2f}) about {q.entity}",
                    priority=q.priority,
                    context={"question_id": q.question_id, "type": q.question_type},
                ))

        return suggestions

    def suggest_from_uncertainty(
        self,
        epistemic_topics: list[str],
        confidence: float,
    ) -> list[ProactiveSuggestion]:
        """
        Suggest verification tasks from epistemic uncertainty.
        """
        suggestions = []
        
        if confidence < 0.4:
             suggestions.append(ProactiveSuggestion(
                type=InitiativeType.CLARIFY,
                description="Request clarification on ambiguities.",
                rationale="Low overall confidence in current understanding.",
                priority=0.9,
            ))
            
        for topic in epistemic_topics:
            suggestions.append(ProactiveSuggestion(
                type=InitiativeType.VERIFY,
                description=f"Verify facts about {topic}",
                rationale="Identified as high uncertainty area.",
                priority=0.8,
            ))
            
        return suggestions

# Global instance
_initiative: InitiativeSystem | None = None

def get_initiative_system() -> InitiativeSystem:
    global _initiative
    if _initiative is None:
        _initiative = InitiativeSystem()
    return _initiative
