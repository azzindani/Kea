"""
Tier 6 Cognitive Load Monitor — Types.

Pydantic models for processing budget measurement, loop/stall detection,
and graduated response actions.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


# ============================================================================
# Cycle Telemetry (input)
# ============================================================================


class CycleTelemetry(BaseModel):
    """Telemetry from a single OODA cycle."""

    cycle_number: int = Field(default=0, ge=0)
    tokens_consumed: int = Field(default=0, ge=0)
    cycle_duration_ms: float = Field(default=0.0, ge=0.0)
    expected_duration_ms: float = Field(default=1000.0, ge=0.0)
    active_module_count: int = Field(default=0, ge=0)
    total_cycles_budget: int = Field(default=100, ge=1)
    total_tokens_budget: int = Field(default=200_000, ge=1)


# ============================================================================
# Cognitive Load Measurement
# ============================================================================


class CognitiveLoad(BaseModel):
    """Three-dimensional load measurement."""

    compute_load: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Tokens + cycles vs budget",
    )
    time_load: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Wall clock vs expected",
    )
    breadth_load: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Active modules vs capacity",
    )
    aggregate: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Weighted aggregate load",
    )


# ============================================================================
# Anomaly Detection
# ============================================================================


class LoopDetection(BaseModel):
    """Result of loop pattern analysis."""

    is_looping: bool = Field(default=False)
    loop_length: int = Field(default=0, ge=0, description="How many decisions repeat")
    loop_count: int = Field(default=0, ge=0, description="How many repetitions")
    repeated_pattern: list[str] = Field(
        default_factory=list,
        description="The repeated decision descriptions",
    )


class OscillationDetection(BaseModel):
    """Result of oscillation pattern analysis."""

    is_oscillating: bool = Field(default=False)
    period: int = Field(default=0, ge=0, description="Oscillation period (2 or 3)")
    conflicting_decisions: list[str] = Field(
        default_factory=list,
        description="The alternating decisions",
    )


class GoalDriftDetection(BaseModel):
    """Result of goal drift analysis."""

    is_drifting: bool = Field(default=False)
    similarity_trend: list[float] = Field(
        default_factory=list,
        description="Recent similarity scores to original objective",
    )
    drift_magnitude: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="How far the agent has drifted",
    )


# ============================================================================
# Response Actions
# ============================================================================


class LoadAction(str, Enum):
    """Graduated response to cognitive load issues."""

    CONTINUE = "continue"     # Normal operation
    SIMPLIFY = "simplify"     # Downgrade pipeline
    ESCALATE = "escalate"     # Ask T5/T7 for help
    ABORT = "abort"           # Kill current cycle


class LoadRecommendation(BaseModel):
    """Recommended action with context."""

    action: LoadAction = Field(...)
    reasoning: str = Field(...)
    load_snapshot: CognitiveLoad = Field(default_factory=CognitiveLoad)
    loop_detected: bool = Field(default=False)
    stall_detected: bool = Field(default=False)
    oscillation_detected: bool = Field(default=False)
    drift_detected: bool = Field(default=False)
