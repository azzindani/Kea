"""
Tier 6 Noise Gate — Types.

Pydantic models for output quality filtering, annotation,
rejection feedback, and retry budget management.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# Tool Output (input from Tier 4)
# ============================================================================


class ToolOutput(BaseModel):
    """Raw output from the OODA loop, pre-filtering."""

    output_id: str = Field(...)
    content: str = Field(default="", description="Output text/data")
    metadata: dict[str, Any] = Field(default_factory=dict)
    source_node_id: str = Field(default="")
    source_dag_id: str = Field(default="")


# ============================================================================
# Quality Metadata (annotation)
# ============================================================================


class QualityMetadata(BaseModel):
    """Quality annotations attached to a passing output."""

    grounding_score: float = Field(default=0.0, ge=0.0, le=1.0)
    calibrated_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    overconfidence_warning: bool = Field(default=False)
    fabricated_claim_count: int = Field(default=0, ge=0)
    source_references: list[str] = Field(
        default_factory=list,
        description="Evidence source IDs for grounded claims",
    )


# ============================================================================
# Filtered Output (pass)
# ============================================================================


class FilteredOutput(BaseModel):
    """An output that passed the noise gate — quality-verified."""

    output_id: str = Field(...)
    content: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)
    quality: QualityMetadata = Field(default_factory=QualityMetadata)
    passed: bool = Field(default=True)


# ============================================================================
# Rejected Output (fail)
# ============================================================================


class RejectionDimension(str, Enum):
    """Which quality dimension caused the rejection."""

    GROUNDING = "grounding"
    CONFIDENCE = "confidence"
    LOAD = "load"
    MULTIPLE = "multiple"


class RetryGuidance(BaseModel):
    """Actionable feedback for Tier 4 when an output fails the gate."""

    rejection_reason: str = Field(...)
    failed_dimensions: list[RejectionDimension] = Field(default_factory=list)
    fabricated_claims: list[str] = Field(
        default_factory=list,
        description="Specific claims that were fabricated",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Suggested actions for improvement",
    )
    retry_count: int = Field(default=0, ge=0)
    should_escalate: bool = Field(
        default=False,
        description="Whether retry budget is exhausted",
    )


class RejectedOutput(BaseModel):
    """An output that failed the noise gate — blocked."""

    output_id: str = Field(...)
    content: str = Field(default="")
    guidance: RetryGuidance = Field(...)
    passed: bool = Field(default=False)


# ============================================================================
# Retry Budget
# ============================================================================


class RetryBudgetStatus(BaseModel):
    """Status of the retry budget for a specific output."""

    output_id: str = Field(...)
    retries_used: int = Field(default=0, ge=0)
    retries_remaining: int = Field(default=3, ge=0)
    should_escalate: bool = Field(default=False)
