"""
Tier 8 Workforce Manager — Types.

Pydantic models for the corporate workforce: mission chunks,
agent handles, workforce pools, scaling decisions, and performance snapshots.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# Mission Chunk — Agent-Assignable Unit of Work
# ============================================================================


class MissionChunk(BaseModel):
    """A discrete, agent-assignable unit of work.

    Produced by T2 decompose_goal() + T3 sequence_and_prioritize()
    at the corporate scope. Each chunk becomes an ExecutableNode
    via T3 assemble_node() during sprint DAG building.
    """

    chunk_id: str = Field(..., description="Unique identifier for this work unit")
    parent_objective_id: str = Field(
        ..., description="ID of the parent mission objective"
    )
    domain: str = Field(
        ...,
        description="Skill domain (e.g., 'backend_development', 'data_analysis')",
    )
    sub_objective: str = Field(
        ..., description="What the specialist should accomplish"
    )
    required_skills: list[str] = Field(
        default_factory=list,
        description="Maps to CognitiveProfile.skills for matching",
    )
    required_tools: list[str] = Field(
        default_factory=list, description="MCP tool categories needed"
    )
    depends_on: list[str] = Field(
        default_factory=list,
        description="Chunk IDs that must complete before this one",
    )
    sprint_number: int = Field(
        default=0, description="Which sprint this chunk belongs to"
    )
    priority: int = Field(
        default=0, ge=0, description="Priority level (0 = highest)"
    )
    token_budget: int = Field(
        default=0, ge=0, description="Max tokens allocated for this chunk"
    )
    cost_budget: float = Field(
        default=0.0, ge=0.0, description="Max cost in dollars for this chunk"
    )
    time_budget_ms: float = Field(
        default=0.0, ge=0.0, description="Max time in milliseconds for this chunk"
    )
    is_parallelizable: bool = Field(
        default=True,
        description="Whether this chunk can run in parallel with siblings",
    )
    pipeline_template_id: str | None = Field(
        default=None, description="For SWARM: shared pipeline reference"
    )
    input_data: dict[str, Any] | None = Field(
        default=None, description="For SWARM: partition-specific data"
    )
    predecessor_artifact_ids: list[str] = Field(
        default_factory=list,
        description="Vault artifact IDs from prior sprints (inter-sprint handoff)",
    )


# ============================================================================
# Agent Lifecycle
# ============================================================================


class AgentStatus(StrEnum):
    """Lifecycle state of a corporate specialist."""

    INITIALIZING = "initializing"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


class TerminationReason(StrEnum):
    """Why a specialist was terminated."""

    MISSION_COMPLETE = "mission_complete"
    IDLE_TIMEOUT = "idle_timeout"
    LOW_QUALITY = "low_quality"
    BUDGET_EXCEEDED = "budget_exceeded"
    STALLED = "stalled"
    REPLACED = "replaced"
    MISSION_ABORTED = "mission_aborted"


# ============================================================================
# Agent Handle & Workforce Pool
# ============================================================================


class AgentHandle(BaseModel):
    """Reference to a hired specialist in the workforce pool."""

    agent_id: str = Field(..., description="Unique agent identifier from Orchestrator")
    profile_id: str = Field(
        ..., description="Cognitive profile used for this specialist"
    )
    role_name: str = Field(
        default="Specialist", description="Human-readable role (e.g., 'Backend Developer')"
    )
    chunk_id: str = Field(
        ..., description="The MissionChunk this agent is assigned to"
    )
    status: AgentStatus = Field(default=AgentStatus.INITIALIZING)
    hired_utc: str = Field(
        default="", description="ISO 8601 timestamp when the agent was hired"
    )
    quality_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Latest quality score"
    )
    total_cost: float = Field(
        default=0.0, ge=0.0, description="Cumulative cost of this agent"
    )


class WorkforcePool(BaseModel):
    """Registry of all active and terminated specialists for a mission."""

    pool_id: str = Field(..., description="Unique pool identifier")
    mission_id: str = Field(..., description="Parent mission ID")
    agents: dict[str, AgentHandle] = Field(
        default_factory=dict, description="agent_id → handle mapping"
    )
    total_hired: int = Field(default=0, ge=0)
    total_fired: int = Field(default=0, ge=0)
    total_cost: float = Field(default=0.0, ge=0.0)
    budget_remaining: float = Field(default=0.0, ge=0.0)


# ============================================================================
# Scaling Decisions
# ============================================================================


class ScaleAction(StrEnum):
    """What workforce action to take."""

    HIRE_MORE = "hire_more"
    FIRE_IDLE = "fire_idle"
    REASSIGN = "reassign"
    HOLD = "hold"


class ScaleDecision(BaseModel):
    """A computed scaling decision (not yet executed)."""

    action: ScaleAction = Field(
        ..., description="The scaling action to perform"
    )
    target_agent_id: str | None = Field(
        default=None, description="Agent to act upon (for FIRE_IDLE/REASSIGN)"
    )
    target_chunk_id: str | None = Field(
        default=None, description="Chunk to assign (for HIRE_MORE/REASSIGN)"
    )
    reason: str = Field(default="", description="Human-readable rationale")


# ============================================================================
# Profile Matching & Performance
# ============================================================================


class ProfileMatch(BaseModel):
    """Result of matching a specialist profile to a mission chunk."""

    agent_profile_id: str = Field(
        ..., description="The matched CognitiveProfile ID"
    )
    chunk_id: str = Field(..., description="The MissionChunk being matched")
    skill_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="T1 scoring skill overlap"
    )
    composite_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Weighted composite match score"
    )
    requires_new_profile: bool = Field(
        default=False,
        description="True if no existing profile meets the threshold",
    )


class PerformanceSnapshot(BaseModel):
    """Performance metrics extracted from a single agent execution."""

    agent_id: str = Field(..., description="Agent whose performance is measured")
    quality_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="From noise gate"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="From calibrator"
    )
    grounding_rate: float = Field(
        default=0.0, ge=0.0, le=1.0, description="From hallucination monitor"
    )
    latency_ms: float = Field(default=0.0, ge=0.0)
    cost: float = Field(default=0.0, ge=0.0)
