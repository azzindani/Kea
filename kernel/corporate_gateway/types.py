"""
Tier 9 — Corporate Gateway Types.

Pydantic models for the Corporation Kernel apex. These types
define the contracts for intent classification, strategic assessment,
response synthesis, and quality grading.

All types are pure data — no HTTP, no I/O.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================


class ClientIntent(StrEnum):
    """Classification of what the client wants."""

    NEW_TASK = "new_task"
    FOLLOW_UP = "follow_up"
    STATUS_CHECK = "status_check"
    REVISION = "revision"
    CONVERSATION = "conversation"
    INTERRUPT = "interrupt"


class ScalingMode(StrEnum):
    """How many agents to deploy."""

    SOLO = "solo"       # 1 agent
    TEAM = "team"       # 2-10 agents
    SWARM = "swarm"     # 10-100K agents


# ============================================================================
# Gate-In Types
# ============================================================================


class SessionState(BaseModel):
    """Persisted session context from Vault."""

    session_id: str = Field(default="")
    client_id: str = Field(default="")
    turns: int = Field(default=0, ge=0)
    active_mission_id: str | None = Field(default=None)
    history_artifact_ids: list[str] = Field(default_factory=list)
    last_intent: str | None = Field(default=None)
    created_utc: str = Field(default="")
    updated_utc: str = Field(default="")


class StrategyAssessment(BaseModel):
    """Result of the strategic assessment phase.

    Produced by ``assess_strategy()`` using T6 activation_router,
    T6 self_model, and shared/hardware.
    """

    complexity: str = Field(
        default="moderate",
        description="From T6 activation_router: trivial | moderate | complex | critical",
    )
    scaling_mode: ScalingMode = Field(default=ScalingMode.SOLO)
    estimated_agents: int = Field(default=1, ge=1)
    estimated_sprints: int = Field(default=1, ge=1)
    estimated_duration_ms: float = Field(default=0.0, ge=0.0)
    hardware_max_parallel: int = Field(
        default=1, ge=1, description="From shared/hardware"
    )
    capability_gaps: list[str] = Field(
        default_factory=list, description="Domains without profiles"
    )
    risk_level: str = Field(
        default="low", description="low | medium | high"
    )


class CorporateGateInResult(BaseModel):
    """Output of Phase 1 (Gate-In)."""

    request_id: str = Field(default="")
    session: SessionState | None = Field(default=None)
    intent: ClientIntent = Field(default=ClientIntent.NEW_TASK)
    strategy: StrategyAssessment | None = Field(default=None)
    chunks: list[dict[str, Any]] | None = Field(
        default=None, description="Serialized MissionChunks"
    )
    sprint_plan: list[dict[str, Any]] | None = Field(
        default=None, description="Serialized Sprint list"
    )
    checkpoint: dict[str, Any] | None = Field(
        default=None, description="Resumable checkpoint state"
    )
    fast_path_response: dict[str, Any] | None = Field(
        default=None,
        description="Non-None signals Gate-Out should skip Execute phase",
    )
    gate_in_duration_ms: float = Field(default=0.0, ge=0.0)


# ============================================================================
# Execute Types
# ============================================================================


class CorporateExecuteResult(BaseModel):
    """Output of Phase 2 (Execute)."""

    mission_id: str | None = Field(default=None)
    mission_result: dict[str, Any] | None = Field(default=None)
    status_report: str | None = Field(
        default=None, description="For STATUS_CHECK fast-path"
    )
    interrupts_handled: int = Field(default=0, ge=0)
    execute_duration_ms: float = Field(default=0.0, ge=0.0)


# ============================================================================
# Gate-Out Types
# ============================================================================


class ResponseSection(BaseModel):
    """A section of the synthesized response."""

    section_id: str = Field(default="")
    title: str = Field(default="")
    content: str = Field(default="")
    domain: str = Field(default="general")
    source_agent_id: str = Field(default="")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class SynthesizedResponse(BaseModel):
    """The merged, human-readable response from all agent artifacts.

    Produced by ``synthesize_response()`` using T3 critique + LLM merge.
    """

    title: str = Field(default="")
    executive_summary: str = Field(default="")
    full_content: str = Field(default="")
    sections: list[ResponseSection] = Field(default_factory=list)
    source_agents: list[str] = Field(default_factory=list)
    confidence_map: dict[str, float] = Field(default_factory=dict)
    gaps: list[str] = Field(default_factory=list)
    is_partial: bool = Field(default=False)


class CorporateQuality(BaseModel):
    """Quality metadata for the final corporate response."""

    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    completeness_pct: float = Field(default=0.0, ge=0.0, le=1.0)
    conflict_free: bool = Field(default=True)
    grounding_score: float = Field(default=0.0, ge=0.0, le=1.0)
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    flags: list[str] = Field(default_factory=list)


class MissionSummary(BaseModel):
    """High-level summary of the mission execution."""

    total_sprints: int = Field(default=0, ge=0)
    completed_sprints: int = Field(default=0, ge=0)
    total_agents: int = Field(default=0, ge=0)
    total_artifacts: int = Field(default=0, ge=0)
    scaling_mode: ScalingMode = Field(default=ScalingMode.SOLO)
    duration_ms: float = Field(default=0.0, ge=0.0)
    was_resumed: bool = Field(default=False)


# ============================================================================
# Interrupt Types
# ============================================================================


class InterruptClassification(BaseModel):
    """Pure-logic classification of a client interrupt."""

    interrupt_type: str = Field(
        default="status_check",
        description="status_check | scope_change | abort",
    )
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning: str = Field(default="")


class InterruptResponse(BaseModel):
    """Response to a client interrupt."""

    interrupt_type: str = Field(default="")
    response_content: str = Field(default="")
    mission_impact: str = Field(
        default="none",
        description="none | paused | adjusted | aborted",
    )
