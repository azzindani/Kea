"""
Tier 5 Lifecycle Controller — Types.

Pydantic models for agent genesis, identity management,
macro-objective tracking, and lifecycle state control.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

# ============================================================================
# Spawn Request (input from Tier 7 via Tier 6)
# ============================================================================


class SpawnRequest(BaseModel):
    """Request from the Corporate Kernel to spawn a new agent."""

    request_id: str = Field(default="default_req_id", description="Unique spawn request identifier")
    role: str = Field(..., description="Assigned role (e.g., 'security_auditor')")
    objective: str = Field(default="default_objective", description="Prime directive / macro-objective")
    profile_id: str = Field(
        default="",
        description="Cognitive profile ID to load from Vault",
    )
    budget_tokens: int = Field(default=0, ge=0, description="Allocated token budget")
    budget_cost: float = Field(default=0.0, ge=0.0, description="Allocated cost budget")
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Initial context from the spawner",
    )


# ============================================================================
# Agent Identity
# ============================================================================


class AgentIdentity(BaseModel):
    """Core identity of a spawned agent."""

    agent_id: str = Field(..., description="Unique agent identifier")
    role: str = Field(..., description="Assigned role")
    profile_id: str = Field(default="", description="Loaded cognitive profile ID")
    created_utc: str = Field(..., description="ISO 8601 UTC genesis timestamp")


# ============================================================================
# Cognitive Profile (loaded from Vault)
# ============================================================================


class CognitiveProfile(BaseModel):
    """Agent persona, skills, rules, and constraints.

    Loaded from Vault at agent genesis; defines role-specific behavior.
    """

    profile_id: str = Field(...)
    role_name: str = Field(..., description="Human-readable role")
    skills: list[str] = Field(default_factory=list, description="Available skill set")
    tools_allowed: list[str] = Field(
        default_factory=list,
        description="MCP tool categories this agent may use",
    )
    tools_forbidden: list[str] = Field(
        default_factory=list,
        description="MCP tool categories this agent must NOT use",
    )
    knowledge_domains: list[str] = Field(
        default_factory=list,
        description="Knowledge domains accessible to this agent",
    )
    ethical_constraints: list[str] = Field(
        default_factory=list,
        description="Non-negotiable ethical rules",
    )
    quality_bar: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum output quality threshold",
    )
    max_parallel_tasks: int = Field(default=4, ge=1)


# ============================================================================
# Identity Context (immutable, enforced downward)
# ============================================================================


class IdentityContext(BaseModel):
    """Immutable identity context passed down to all lower tiers.

    Once set during genesis, this cannot be modified by any
    lower-tier component.
    """

    agent_id: str = Field(...)
    role: str = Field(...)
    skills: frozenset[str] = Field(default_factory=frozenset)
    tools_allowed: frozenset[str] = Field(default_factory=frozenset)
    tools_forbidden: frozenset[str] = Field(default_factory=frozenset)
    knowledge_domains: frozenset[str] = Field(default_factory=frozenset)
    ethical_constraints: tuple[str, ...] = Field(default_factory=tuple)
    quality_bar: float = Field(default=0.7, ge=0.0, le=1.0)

    class Config:
        frozen = True


# ============================================================================
# Lifecycle Signal & State
# ============================================================================


class LifecycleSignalType(StrEnum):
    """Types of lifecycle control signals."""

    START = "start"         # Begin OODA loop execution
    PAUSE = "pause"         # Suspend loop, preserve state
    PANIC = "panic"         # Network failure, deep sleep + periodic retry
    TERMINATE = "terminate"  # Graceful shutdown with epoch commit
    RESUME = "resume"       # Resume from suspended/sleeping state


class LifecycleSignal(BaseModel):
    """A lifecycle control signal."""

    signal_type: LifecycleSignalType = Field(...)
    reason: str = Field(default="", description="Why this signal was issued")
    payload: dict[str, Any] = Field(default_factory=dict)


class LifecyclePhase(StrEnum):
    """Macro-level agent lifecycle phases."""

    INITIALIZING = "initializing"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    SLEEPING = "sleeping"
    PANICKING = "panicking"
    TERMINATED = "terminated"


class LifecycleState(BaseModel):
    """Current lifecycle state of the agent."""

    phase: LifecyclePhase = Field(...)
    previous_phase: LifecyclePhase | None = Field(default=None)
    reason: str = Field(default="")
    transitioned_utc: str = Field(..., description="ISO 8601 UTC timestamp")


# ============================================================================
# Macro-Objective Tracking
# ============================================================================


class ObjectiveStatus(StrEnum):
    """Status of a macro-objective."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ObjectiveState(BaseModel):
    """Tracking state for a single macro-objective."""

    objective_id: str = Field(...)
    description: str = Field(...)
    status: ObjectiveStatus = Field(default=ObjectiveStatus.PENDING)
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    epochs_consumed: int = Field(default=0, ge=0)
    sub_objectives_completed: int = Field(default=0, ge=0)
    sub_objectives_total: int = Field(default=0, ge=0)


# ============================================================================
# Agent Lifecycle (top-level output)
# ============================================================================


class AgentLifecycle(BaseModel):
    """Final lifecycle report returned to Tier 6/7."""

    agent_id: str = Field(...)
    identity: AgentIdentity = Field(...)
    final_phase: LifecyclePhase = Field(...)
    objectives_completed: list[str] = Field(default_factory=list)
    objectives_failed: list[str] = Field(default_factory=list)
    total_epochs: int = Field(default=0, ge=0)
    total_cost: float = Field(default=0.0, ge=0.0)
    total_tokens: int = Field(default=0, ge=0)
    total_duration_ms: float = Field(default=0.0, ge=0.0)
