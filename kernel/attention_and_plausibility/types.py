"""
Tier 2 Attention & Plausibility — Types.

Pydantic models for cognitive filtering:
attention masking and plausibility/sanity checking.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class PlausibilityVerdict(str, Enum):
    """Result of plausibility check."""

    PASS = "pass"       # Task is logically coherent and achievable
    FAIL = "fail"       # Task is contradictory, impossible, or hallucinatory


class TaskState(BaseModel):
    """Incoming task context to be filtered and verified.

    Contains the raw goal with all surrounding context elements.
    """

    goal: str = Field(..., description="The active goal")
    context_elements: list[ContextElement] = Field(
        default_factory=list,
        description="All context items available for the task",
    )
    interpreted_intent: str = Field(
        default="",
        description="T1 intent detection result",
    )


class ContextElement(BaseModel):
    """A single piece of context information."""

    key: str = Field(..., description="Context variable name")
    value: str = Field(..., description="Context variable value")
    source: str = Field(default="unknown", description="Where this context came from")
    relevance: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Computed relevance to the goal",
    )


# Fix forward reference
TaskState.model_rebuild()


class FilteredState(BaseModel):
    """Output from attention filtering — only critical variables remain."""

    goal: str = Field(..., description="The active goal (unchanged)")
    critical_elements: list[ContextElement] = Field(
        default_factory=list,
        description="Context elements above relevance threshold",
    )
    dropped_count: int = Field(
        default=0,
        ge=0,
        description="Number of context elements filtered out",
    )


class PlausibilityResult(BaseModel):
    """Result of the plausibility/sanity check."""

    verdict: PlausibilityVerdict = Field(..., description="Pass or fail")
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the verdict",
    )
    issues: list[str] = Field(
        default_factory=list,
        description="Specific issues found (for FAIL verdict)",
    )


class RefinedState(BaseModel):
    """Final cleaned and verified goal context for Tier 3."""

    goal: str = Field(..., description="The verified goal")
    critical_elements: list[ContextElement] = Field(default_factory=list)
    plausibility_confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class SanityAlert(BaseModel):
    """Task rejection alert — goal is implausible or contradictory."""

    reason: str = Field(..., description="Why the task was rejected")
    issues: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    original_goal: str = Field(default="")
