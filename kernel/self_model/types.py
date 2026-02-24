"""
Tier 6 Self Model — Types.

Pydantic models for the agent's internal representation of itself:
capability maps, cognitive state, and accuracy tracking.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# Signal Tags (input from Tier 1)
# ============================================================================


class SignalTags(BaseModel):
    """Tags extracted from a signal by Tier 1 classification."""

    urgency: str = Field(default="normal", description="low, normal, high, critical")
    domain: str = Field(default="general", description="Knowledge domain")
    complexity: str = Field(default="simple", description="Structural complexity hint")
    source_type: str = Field(default="user", description="user, tool, agent, system")
    intent: str = Field(default="unknown", description="Detected intent label")
    entity_count: int = Field(default=0, ge=0)
    required_skills: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)


# ============================================================================
# Capability Assessment
# ============================================================================


class CapabilityGap(BaseModel):
    """What the agent is missing to handle a signal."""

    missing_tools: list[str] = Field(default_factory=list)
    missing_knowledge: list[str] = Field(default_factory=list)
    constraint_violations: list[str] = Field(
        default_factory=list,
        description="Role boundaries that would be violated",
    )
    severity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="How severe the gap is (1.0 = completely unable)",
    )


class CapabilityAssessment(BaseModel):
    """Result of assessing whether the agent can handle a signal."""

    can_handle: bool = Field(..., description="Overall capability verdict")
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in the assessment",
    )
    gap: CapabilityGap | None = Field(
        default=None,
        description="Details of what's missing (if not fully capable)",
    )
    partial_capabilities: list[str] = Field(
        default_factory=list,
        description="Things the agent CAN do for this signal",
    )


# ============================================================================
# Cognitive State Tracker
# ============================================================================


class ProcessingPhase(str, Enum):
    """Which T6 temporal phase the agent is in."""

    PRE_EXECUTION = "pre_execution"
    DURING_EXECUTION = "during_execution"
    POST_EXECUTION = "post_execution"
    IDLE = "idle"


class AgentCognitiveState(BaseModel):
    """Real-time snapshot of the agent's own cognitive processing."""

    agent_id: str = Field(default="")
    processing_phase: ProcessingPhase = Field(default=ProcessingPhase.IDLE)
    active_modules: list[str] = Field(
        default_factory=list,
        description="Currently active module names",
    )
    current_task_description: str = Field(default="")
    ooda_cycle_count: int = Field(default=0, ge=0)
    elapsed_ms: float = Field(default=0.0, ge=0.0)
    current_dag_id: str | None = Field(default=None)


# ============================================================================
# Accuracy & Calibration History
# ============================================================================


class CalibrationDataPoint(BaseModel):
    """A single prediction-vs-actual data point."""

    predicted: float = Field(..., ge=0.0, le=1.0)
    actual: float = Field(..., ge=0.0, le=1.0)
    domain: str = Field(default="general")
    timestamp_utc: str = Field(default="")


class CalibrationHistory(BaseModel):
    """Running calibration history for the Confidence Calibrator."""

    data_points: list[CalibrationDataPoint] = Field(default_factory=list)
    domain_accuracy: dict[str, float] = Field(
        default_factory=dict,
        description="Per-domain accuracy rates",
    )
    overall_accuracy: float = Field(default=0.5, ge=0.0, le=1.0)
    sample_count: int = Field(default=0, ge=0)


class CalibrationCurve(BaseModel):
    """Maps stated confidence bins to observed accuracy rates."""

    domain: str = Field(default="general")
    bin_mapping: dict[str, float] = Field(
        default_factory=dict,
        description="Stated confidence bin → observed accuracy",
    )
    sample_count: int = Field(default=0, ge=0)
    last_updated_utc: str = Field(default="")
