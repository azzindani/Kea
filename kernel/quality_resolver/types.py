"""
Tier 8 Quality Resolver — Types.

Pydantic models for multi-agent quality control: conflicts,
resolutions, quality audits, and final mission quality reports.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ============================================================================
# Conflict Detection
# ============================================================================


class Conflict(BaseModel):
    """A detected contradiction between two agent outputs."""

    artifact_a_id: str = Field(
        ..., description="First conflicting artifact ID"
    )
    artifact_b_id: str = Field(
        ..., description="Second conflicting artifact ID"
    )
    description: str = Field(
        default="", description="What the conflict is about"
    )
    severity: str = Field(
        default="medium",
        description="Severity level: low | medium | high | critical",
    )


# ============================================================================
# Conflict Resolution
# ============================================================================


class Resolution(BaseModel):
    """Result of resolving a detected conflict."""

    conflict_id: str = Field(
        default="", description="Optional reference to conflict"
    )
    strategy_used: str = Field(
        default="consensus",
        description="consensus | weighted_vote | arbitration | escalation",
    )
    winning_artifact_id: str = Field(
        default="", description="The artifact chosen as correct"
    )
    justification: str = Field(
        default="", description="Why this resolution was chosen"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence in resolution"
    )


# ============================================================================
# Quality Audit
# ============================================================================


class QualityAudit(BaseModel):
    """Quality assessment for a single sprint's output."""

    sprint_id: str = Field(..., description="Sprint being audited")
    avg_quality: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Average from noise gate"
    )
    avg_confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Average from calibrator"
    )
    avg_grounding: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Average from hallucination monitor",
    )
    issues: list[str] = Field(
        default_factory=list, description="Quality issues found"
    )
    overall: str = Field(
        default="pass", description="pass | warning | fail"
    )


# ============================================================================
# Final Mission Quality Report
# ============================================================================


class FinalQualityReport(BaseModel):
    """Comprehensive quality report across all mission sprints."""

    mission_id: str = Field(..., description="Mission being assessed")
    conflicts_found: int = Field(default=0, ge=0)
    conflicts_resolved: int = Field(default=0, ge=0)
    completeness_pct: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Fraction of chunks that produced valid output",
    )
    confidence_map: dict[str, float] = Field(
        default_factory=dict,
        description="chunk_id → confidence score",
    )
    gaps: list[str] = Field(
        default_factory=list,
        description="Knowledge or coverage gaps identified",
    )
    overall_quality: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Weighted average quality across all audits",
    )
