"""
Tier 4 Short-Term Memory — Types.

Pydantic models for the ephemeral RAM of the OODA loop:
DAG state tracking, event history, and entity caching.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

# ============================================================================
# Observation Events
# ============================================================================


class EventSource(StrEnum):
    """Where an observation event originated."""

    USER = "user"           # User message / input
    MCP_TOOL = "mcp_tool"   # MCP tool response
    RAG = "rag"             # RAG service update
    ARTIFACT_BUS = "artifact_bus"  # Inter-agent artifact
    SYSTEM = "system"       # System health / internal event
    WEBHOOK = "webhook"     # External webhook trigger


class ObservationEvent(BaseModel):
    """A single event observed by the OODA loop's Observe phase."""

    event_id: str = Field(..., description="Unique event identifier")
    source: EventSource = Field(...)
    description: str = Field(..., description="Human-readable event summary")
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Event-specific data",
    )
    timestamp_utc: str = Field(..., description="ISO 8601 UTC timestamp")
    priority: int = Field(
        default=0,
        ge=0,
        description="Event priority (higher = more urgent)",
    )


# ============================================================================
# DAG State Tracking
# ============================================================================


class NodeExecutionStatus(StrEnum):
    """Status of a specific node within a DAG."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARKED = "parked"       # Waiting on async result


class DagStateSnapshot(BaseModel):
    """Current progress snapshot of a DAG execution."""

    dag_id: str = Field(...)
    total_nodes: int = Field(default=0, ge=0)
    completed_count: int = Field(default=0, ge=0)
    failed_count: int = Field(default=0, ge=0)
    pending_count: int = Field(default=0, ge=0)
    running_count: int = Field(default=0, ge=0)
    node_statuses: dict[str, NodeExecutionStatus] = Field(
        default_factory=dict,
        description="Per-node status map (node_id → status)",
    )
    completion_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )
    failed_node_ids: list[str] = Field(default_factory=list)
    estimated_remaining_steps: int = Field(default=0, ge=0)


# ============================================================================
# Entity Cache
# ============================================================================


class CachedEntity(BaseModel):
    """A temporarily cached entity extracted during an OODA cycle."""

    key: str = Field(..., description="Lookup key")
    value: Any = Field(..., description="Cached value")
    ttl_seconds: int | None = Field(
        default=None,
        description="Time-to-live in seconds (None = no expiry)",
    )
    created_utc: str = Field(..., description="ISO 8601 UTC creation timestamp")
    source_event_id: str = Field(
        default="",
        description="Event that produced this entity",
    )


# ============================================================================
# Context Slice (read_context output)
# ============================================================================


class ContextSlice(BaseModel):
    """A snapshot of the working memory for the Orient phase."""

    dag_snapshots: list[DagStateSnapshot] = Field(
        default_factory=list,
        description="Active DAG state snapshots",
    )
    recent_events: list[ObservationEvent] = Field(
        default_factory=list,
        description="Most recent observation events",
    )
    cached_entities: dict[str, Any] = Field(
        default_factory=dict,
        description="Currently cached entity key-value pairs",
    )
    total_events_in_history: int = Field(default=0, ge=0)
    total_entities_cached: int = Field(default=0, ge=0)


# ============================================================================
# Epoch Summary (flush output)
# ============================================================================


class EpochSummary(BaseModel):
    """Compressed summary of Short-Term Memory at epoch end.

    Passed to Tier 5 for permanent storage in the Vault.
    """

    epoch_id: str = Field(..., description="Unique epoch identifier")
    dag_ids_processed: list[str] = Field(default_factory=list)
    total_events_processed: int = Field(default=0, ge=0)
    total_entities_cached: int = Field(default=0, ge=0)
    completed_dags: int = Field(default=0, ge=0)
    failed_dags: int = Field(default=0, ge=0)
    key_events: list[str] = Field(
        default_factory=list,
        description="Summarized descriptions of significant events",
    )
    key_entities: dict[str, Any] = Field(
        default_factory=dict,
        description="Most important cached entities to preserve",
    )
    total_duration_ms: float = Field(default=0.0, ge=0.0)
