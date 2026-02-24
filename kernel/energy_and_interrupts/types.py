"""
Tier 5 Energy & Interrupts — Types.

Pydantic models for budget tracking, interrupt handling,
and lifecycle state transitions.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# Cost Events (input from Tier 4 telemetry)
# ============================================================================


class CostDimension(str, Enum):
    """Categories of resource consumption."""

    API_TOKENS = "api_tokens"
    COMPUTE_MS = "compute_ms"
    DB_WRITES = "db_writes"
    NETWORK_CALLS = "network_calls"


class CostEvent(BaseModel):
    """A single cost event from Tier 4 execution."""

    event_id: str = Field(...)
    dimension: CostDimension = Field(...)
    amount: float = Field(..., ge=0.0, description="Amount consumed")
    source_node_id: str = Field(default="", description="Which DAG node generated this cost")
    timestamp_utc: str = Field(..., description="ISO 8601 UTC timestamp")


# ============================================================================
# Budget State
# ============================================================================


class BudgetState(BaseModel):
    """Running budget tracker."""

    total_tokens_consumed: int = Field(default=0, ge=0)
    total_cost_consumed: float = Field(default=0.0, ge=0.0)
    total_compute_ms: float = Field(default=0.0, ge=0.0)
    total_db_writes: int = Field(default=0, ge=0)
    total_network_calls: int = Field(default=0, ge=0)
    epoch_tokens_consumed: int = Field(default=0, ge=0)
    token_limit: int = Field(default=0, ge=0, description="Assigned token budget")
    cost_limit: float = Field(default=0.0, ge=0.0, description="Assigned cost budget")
    burn_rate_tokens_per_second: float = Field(
        default=0.0,
        ge=0.0,
        description="Current token consumption rate",
    )
    utilization: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Budget utilization ratio (consumed / limit)",
    )


# ============================================================================
# Interrupt Signals (from Tier 7 via Tier 6)
# ============================================================================


class InterruptType(str, Enum):
    """Types of corporate interrupt signals."""

    PRIORITY_OVERRIDE = "priority_override"  # Drop current, start new task
    KILL = "kill"                            # Immediate graceful termination
    BUDGET_GRANT = "budget_grant"            # Resume from suspended
    RECONFIGURE = "reconfigure"              # Reload profile/constraints


class InterruptSignal(BaseModel):
    """A top-down control signal from Corporate Kernel."""

    interrupt_id: str = Field(...)
    interrupt_type: InterruptType = Field(...)
    reason: str = Field(default="")
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Type-specific data (e.g., new objective for PRIORITY_OVERRIDE)",
    )
    priority: int = Field(default=0, ge=0, description="Signal priority")
    timestamp_utc: str = Field(..., description="ISO 8601 UTC timestamp")


class InterruptAction(str, Enum):
    """What the lifecycle manager should do in response to an interrupt."""

    SWITCH_OBJECTIVE = "switch_objective"
    TERMINATE = "terminate"
    RESUME = "resume"
    RELOAD_PROFILE = "reload_profile"
    IGNORE = "ignore"


# ============================================================================
# Control Triggers & Transitions
# ============================================================================


class ControlTriggerSource(str, Enum):
    """What triggered a lifecycle transition."""

    BUDGET_EXHAUSTED = "budget_exhausted"
    INTERRUPT_RECEIVED = "interrupt_received"
    OODA_COMPLETE = "ooda_complete"
    PANIC_DETECTED = "panic_detected"
    NETWORK_RESTORED = "network_restored"
    MANUAL_OVERRIDE = "manual_override"


class ControlTrigger(BaseModel):
    """A trigger that initiates a lifecycle state transition."""

    source: ControlTriggerSource = Field(...)
    description: str = Field(default="")
    payload: dict[str, Any] = Field(default_factory=dict)


class LifecycleTransition(BaseModel):
    """Record of a lifecycle state transition (for audit logging)."""

    from_phase: str = Field(...)
    to_phase: str = Field(...)
    trigger: ControlTrigger = Field(...)
    timestamp_utc: str = Field(...)
    agent_id: str = Field(default="")


# ============================================================================
# Control Decision (top-level output)
# ============================================================================


class ControlAction(str, Enum):
    """Top-level control actions."""

    CONTINUE = "continue"       # Budget OK, no interrupts
    SUSPEND = "suspend"         # Budget exhausted or pause requested
    TERMINATE = "terminate"     # Kill signal or graceful shutdown
    SWITCH = "switch"           # Priority override — new objective
    PANIC = "panic"             # Unrecoverable error, deep sleep


class ControlDecision(BaseModel):
    """Decision from the energy authority about what to do next."""

    action: ControlAction = Field(...)
    reasoning: str = Field(...)
    budget_state: BudgetState = Field(default_factory=BudgetState)
    new_objective: str | None = Field(
        default=None,
        description="New objective (for SWITCH action)",
    )
