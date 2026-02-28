"""
Tier 4 OODA Loop — Types.

Pydantic models for the Observe-Orient-Decide-Act execution engine:
cycle results, decisions, action results, and loop state.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

# ObservationEvent is defined in short_term_memory and re-exported here
# so callers can import it from either module.
from kernel.short_term_memory.types import ObservationEvent as ObservationEvent

# ============================================================================
# Agent State (the central state object flowing through the loop)
# ============================================================================


class AgentStatus(StrEnum):
    """Macro lifecycle status of the agent within the OODA loop."""

    ACTIVE = "active"       # Executing cycles
    BLOCKED = "blocked"     # Waiting on external dependency
    PARKED = "parked"       # DAG parked, context switched
    SLEEPING = "sleeping"   # Deep sleep (Tier 5)
    TERMINATED = "terminated"


class MacroObjective(BaseModel):
    """A high-level goal the agent is working toward."""

    objective_id: str = Field(default="default_obj_id")
    description: str = Field(...)
    priority: int = Field(default=0, ge=0, description="Lower = higher priority")
    completed: bool = Field(default=False)


class AgentState(BaseModel):
    """Central state object that flows through every OODA cycle.

    Progressively mutated by each phase (Observe, Orient, Decide, Act).
    """

    agent_id: str = Field(..., description="Unique agent identifier")
    status: AgentStatus = Field(default=AgentStatus.ACTIVE)
    current_objectives: list[MacroObjective] = Field(default_factory=list)
    active_dag_id: str | None = Field(
        default=None,
        description="Currently executing DAG ID",
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Accumulated context from Orient phase",
    )
    cycle_count: int = Field(default=0, ge=0, description="Total cycles executed")
    total_cost: float = Field(default=0.0, ge=0.0, description="Accumulated cost")


# ============================================================================
# Observe Phase Output
# ============================================================================

# ObservationEvent is defined in short_term_memory/types.py and reused here.
# Import it from kernel.short_term_memory.types when needed.


class EventStream(BaseModel):
    """Abstraction over the event source polled during Observe."""

    stream_id: str = Field(..., description="Stream identifier")
    source_urls: list[str] = Field(
        default_factory=list,
        description="Service endpoints to poll (MCP, RAG, etc.)",
    )
    poll_timeout_ms: float = Field(
        default=1000.0,
        ge=0.0,
        description="Maximum time to wait for events",
    )


# ============================================================================
# Orient Phase Output
# ============================================================================


class OrientedState(BaseModel):
    """Contextualized state produced by the Orient phase.

    Merges new observations with existing knowledge (from RAG)
    and working context.
    """

    is_blocked: bool = Field(
        default=False,
        description="Whether a blocking condition was detected",
    )
    blocking_reason: str = Field(
        default="",
        description="Why the agent is blocked (if applicable)",
    )
    enriched_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Context after RAG enrichment",
    )
    observation_summary: str = Field(
        default="",
        description="Summary of new observations",
    )
    state_changes: list[str] = Field(
        default_factory=list,
        description="Detected environmental state changes",
    )


# ============================================================================
# Decide Phase Output
# ============================================================================


class DecisionAction(StrEnum):
    """What the Decide phase tells the Act phase to do."""

    CONTINUE = "continue"       # Execute next node in current DAG
    REPLAN = "replan"           # Request new DAG from Tier 3
    PARK = "park"               # Park current DAG, switch context
    COMPLETE = "complete"       # Objective achieved, stop loop
    SLEEP = "sleep"             # No actionable work, request sleep


class Decision(BaseModel):
    """Output of the Decide phase."""

    action: DecisionAction = Field(...)
    reasoning: str = Field(..., description="Why this decision was made")
    target_node_ids: list[str] = Field(
        default_factory=list,
        description="Node IDs to execute (for CONTINUE)",
    )
    replan_objective: str = Field(
        default="",
        description="New objective for Tier 3 (for REPLAN)",
    )
    replan_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Context to pass to Tier 3 replanner",
    )


# ============================================================================
# Act Phase Output
# ============================================================================


class ActionResult(BaseModel):
    """Output of the Act phase after executing DAG node(s)."""

    node_id: str = Field(..., description="Which node was executed")
    success: bool = Field(default=True)
    outputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Node output key-value pairs",
    )
    error_message: str = Field(default="")
    duration_ms: float = Field(default=0.0, ge=0.0)
    cost: float = Field(default=0.0, ge=0.0)
    is_async: bool = Field(
        default=False,
        description="Whether this returned a deferred/async result",
    )
    job_id: str | None = Field(
        default=None,
        description="Async job ID (if is_async=True)",
    )
    polling_url: str | None = Field(
        default=None,
        description="Polling URL for async result (if applicable)",
    )


# ============================================================================
# Cycle & Loop Results
# ============================================================================


class CycleAction(StrEnum):
    """What the loop should do after a cycle completes."""

    CONTINUE = "continue"   # Run another cycle
    PARK = "park"           # Park and context-switch
    TERMINATE = "terminate"  # Stop the loop entirely
    SLEEP = "sleep"         # Enter deep sleep


class CycleResult(BaseModel):
    """Output of a single OODA cycle."""

    cycle_number: int = Field(default=0, ge=0)
    next_action: CycleAction = Field(default=CycleAction.CONTINUE)
    action_results: list[ActionResult] = Field(default_factory=list)
    state_snapshot: dict[str, Any] = Field(
        default_factory=dict,
        description="Agent state at cycle end",
    )
    artifacts_produced: list[str] = Field(
        default_factory=list,
        description="IDs of artifacts created during this cycle",
    )


class LoopTerminationReason(StrEnum):
    """Why the OODA loop terminated."""

    OBJECTIVE_COMPLETE = "objective_complete"
    MAX_CYCLES_REACHED = "max_cycles_reached"
    LIFECYCLE_SIGNAL = "lifecycle_signal"    # Tier 5 said stop
    ALL_DAGS_PARKED = "all_dags_parked"
    UNRECOVERABLE_ERROR = "unrecoverable_error"


class LoopResult(BaseModel):
    """Final output of the complete OODA loop run."""

    agent_id: str = Field(...)
    total_cycles: int = Field(default=0, ge=0)
    termination_reason: LoopTerminationReason = Field(...)
    final_state: dict[str, Any] = Field(default_factory=dict)
    total_duration_ms: float = Field(default=0.0, ge=0.0)
    total_cost: float = Field(default=0.0, ge=0.0)
    objectives_completed: list[str] = Field(
        default_factory=list,
        description="IDs of completed macro objectives",
    )
    artifacts_produced: list[str] = Field(default_factory=list)
    action_outputs: list[str] = Field(
        default_factory=list,
        description="Text outputs collected from all actions in the loop"
    )
