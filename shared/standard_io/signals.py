"""
Kernel Standard I/O — Signal Factory Functions.

All Signal creation flows through these factories. Direct construction of Signal
is discouraged — these functions generate IDs, stamp timestamps, and merge
default tags to ensure consistency across the entire kernel.

ID Generation:
    Delegates to shared.id_and_hash.generate_id("signal") which produces
    ULID-based, time-sortable, Stripe-prefixed identifiers (sig_<ULID>).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.id_and_hash import generate_id

from .types import KernelError, ModuleRef, Signal, SignalKind


# ============================================================================
# Universal Factory
# ============================================================================


def create_signal(
    kind: SignalKind,
    body: dict[str, Any],
    origin: ModuleRef,
    trace_id: str,
    tags: dict[str, str] | None = None,
    parent_id: str | None = None,
) -> Signal:
    """Universal signal factory — generates ID, stamps timestamp.

    This is the ONLY recommended way to create a Signal. It:
    1. Generates a unique, time-sortable ID (sig_ prefix)
    2. Stamps the current UTC timestamp
    3. Merges caller tags with default origin tags (tier, module)

    Args:
        kind: What the signal carries (TEXT, DATA, FILE, COMMAND, STREAM).
        body: The payload dict, typed by kind convention.
        origin: ModuleRef identifying the creator.
        trace_id: Correlation ID for the full pipeline.
        tags: Optional metadata tags (merged with defaults).
        parent_id: ID of the signal that triggered this one (lineage).

    Returns:
        A new, immutable Signal instance.
    """
    merged_tags: dict[str, str] = {
        "tier": str(origin.tier),
        "module": origin.module,
    }
    if tags:
        merged_tags.update(tags)

    return Signal(
        id=generate_id("signal"),
        kind=kind,
        body=body,
        origin=origin,
        trace_id=trace_id,
        tags=merged_tags,
        created_at=datetime.utcnow(),
        parent_id=parent_id,
    )


# ============================================================================
# Convenience Factories
# ============================================================================


def create_text_signal(
    text: str,
    origin: ModuleRef,
    trace_id: str,
    tags: dict[str, str] | None = None,
) -> Signal:
    """Convenience: TEXT signal from a string.

    Used by T4 (OODA Act output), T6 (noise gate filtered output),
    and T7 (team orchestration messages).
    """
    return create_signal(
        kind=SignalKind.TEXT,
        body={"text": text},
        origin=origin,
        trace_id=trace_id,
        tags=tags,
    )


def create_data_signal(
    data: Any,
    schema: str,
    origin: ModuleRef,
    trace_id: str,
    tags: dict[str, str] | None = None,
) -> Signal:
    """Convenience: DATA signal from typed data.

    The schema string is a type hint (e.g., "list[AtomicInsight]",
    "ClassificationResult") enabling downstream modules to validate
    before parsing.

    Args:
        data: The structured data payload.
        schema: Type hint string for downstream validation.
        origin: ModuleRef identifying the creator.
        trace_id: Correlation ID for the full pipeline.
        tags: Optional metadata tags.

    Returns:
        A new Signal with kind=DATA.
    """
    body: dict[str, Any] = {"data": data, "schema": schema}
    if isinstance(data, list):
        body["count"] = len(data)
    return create_signal(
        kind=SignalKind.DATA,
        body=body,
        origin=origin,
        trace_id=trace_id,
        tags=tags,
    )


def create_file_signal(
    file_id: str,
    file_type: str,
    path: str | None,
    origin: ModuleRef,
    trace_id: str,
) -> Signal:
    """Convenience: FILE signal from a reference.

    The file itself is NOT embedded in the signal — only the reference.
    Actual file access goes through the Vault Service or MCP Host.
    """
    return create_signal(
        kind=SignalKind.FILE,
        body={"file_id": file_id, "file_type": file_type, "path": path},
        origin=origin,
        trace_id=trace_id,
    )


def create_command_signal(
    action: str,
    target: ModuleRef,
    origin: ModuleRef,
    trace_id: str,
    payload: dict[str, Any] | None = None,
) -> Signal:
    """Convenience: COMMAND signal for control flow.

    Standard actions:
        "activate" — wake a module
        "sleep"    — suspend a module
        "retry"    — re-execute with feedback
        "abort"    — kill current cycle
        "pivot"    — change objective

    Used by T5 (lifecycle), T6 (activation router, load monitor),
    T7 (team orchestrator).
    """
    body: dict[str, Any] = {
        "action": action,
        "target": target.model_dump(),
    }
    if payload:
        body.update(payload)
    return create_signal(
        kind=SignalKind.COMMAND,
        body=body,
        origin=origin,
        trace_id=trace_id,
    )


def create_error_signal(
    error: KernelError,
    origin: ModuleRef,
    trace_id: str,
) -> Signal:
    """Wrap a KernelError as a signal for pipeline propagation.

    Used when an error needs to flow through the signal pipeline
    (e.g., for T6 noise gate evaluation or T7 team communication)
    rather than being returned as a Result.error.
    """
    return create_signal(
        kind=SignalKind.DATA,
        body={"data": error.model_dump(), "schema": "KernelError"},
        origin=origin,
        trace_id=trace_id,
        tags={"error_code": error.code, "severity": error.severity.value},
    )
