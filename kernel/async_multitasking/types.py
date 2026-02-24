"""
Tier 4 Async Multitasking — Types.

Pydantic models for DAG parking, context switching, wait listeners,
and deep sleep delegation.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# Parking & Wait State
# ============================================================================


class ParkingTicket(BaseModel):
    """Receipt for a parked DAG, enabling later resumption."""

    ticket_id: str = Field(..., description="Unique parking ticket identifier")
    dag_id: str = Field(..., description="Parked DAG identifier")
    parked_at_node_id: str = Field(
        ...,
        description="Node where execution was suspended",
    )
    resume_event_type: str = Field(
        ...,
        description="Event type that will trigger unparking",
    )
    state_snapshot: dict[str, Any] = Field(
        default_factory=dict,
        description="Serialized DAG state at parking time",
    )
    parked_utc: str = Field(..., description="ISO 8601 UTC timestamp of parking")
    priority: int = Field(
        default=0,
        ge=0,
        description="Priority for resumption ordering",
    )


class WaitMode(str, Enum):
    """How the system waits for the parked task to complete."""

    WEBHOOK = "webhook"     # External service pushes completion
    POLL = "poll"           # Periodic polling for completion
    TIMER = "timer"         # Wake after fixed duration


class WaitHandle(BaseModel):
    """Handle for a registered wait listener."""

    handle_id: str = Field(..., description="Unique handle identifier")
    ticket_id: str = Field(..., description="Associated parking ticket")
    wait_mode: WaitMode = Field(...)
    poll_url: str | None = Field(
        default=None,
        description="URL to poll (for POLL mode)",
    )
    poll_interval_ms: float = Field(
        default=2000.0,
        ge=0.0,
        description="Polling interval in ms",
    )
    webhook_endpoint: str | None = Field(
        default=None,
        description="Webhook callback URL (for WEBHOOK mode)",
    )
    timer_ms: float | None = Field(
        default=None,
        ge=0.0,
        description="Timer duration in ms (for TIMER mode)",
    )
    registered_utc: str = Field(..., description="ISO 8601 UTC registration timestamp")


# ============================================================================
# DAG Queue
# ============================================================================


class DAGQueueEntry(BaseModel):
    """An entry in the active DAG queue."""

    dag_id: str = Field(...)
    priority: int = Field(default=0, ge=0)
    is_parked: bool = Field(default=False)
    parking_ticket: ParkingTicket | None = Field(default=None)
    description: str = Field(default="")


class DAGQueue(BaseModel):
    """Priority queue of DAGs available for execution."""

    entries: list[DAGQueueEntry] = Field(default_factory=list)
    max_capacity: int = Field(default=32, ge=1)


# ============================================================================
# Context Switch & Sleep
# ============================================================================


class NextActionKind(str, Enum):
    """What the OODA loop should do after async task management."""

    CONTINUE_CURRENT = "continue_current"   # Keep going with current DAG
    SWITCH_CONTEXT = "switch_context"       # Load a different DAG
    DEEP_SLEEP = "deep_sleep"               # No actionable work


class NextAction(BaseModel):
    """Directive returned by the async task manager."""

    kind: NextActionKind = Field(...)
    target_dag_id: str | None = Field(
        default=None,
        description="DAG to switch to (for SWITCH_CONTEXT)",
    )
    reasoning: str = Field(default="", description="Why this action was chosen")


class SleepToken(BaseModel):
    """Confirmation that the agent has entered deep sleep."""

    token_id: str = Field(..., description="Unique sleep token")
    wake_triggers: list[str] = Field(
        default_factory=list,
        description="Event types that will wake the agent",
    )
    parked_dag_count: int = Field(default=0, ge=0)
    entered_sleep_utc: str = Field(..., description="ISO 8601 UTC timestamp")
