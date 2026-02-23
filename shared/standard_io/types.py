"""
Kernel Standard I/O — Core Types.

Defines the three core types of the kernel communication protocol:
- Signal: The atomic, immutable data unit flowing through the kernel.
- Result: The universal return type for every kernel function.
- KernelError: Structured failure — first-class data, not an exception.

Supporting types: ModuleRef, Metrics, and all related enumerations.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Enumerations
# ============================================================================


class SignalKind(str, Enum):
    """What the signal carries."""

    TEXT = "text"          # Natural language (for LLM / display)
    DATA = "data"          # Structured data (dict, list, Pydantic model)
    FILE = "file"          # File reference (path, URL, binary ref)
    COMMAND = "command"     # Control instruction (activate, sleep, retry)
    STREAM = "stream"      # Streaming chunk (partial data, SSE events)


class ResultStatus(str, Enum):
    """Outcome of a kernel function."""

    OK = "ok"              # Fully successful
    PARTIAL = "partial"    # Partially successful (some signals, some errors)
    ERROR = "error"        # Failed — error field is populated
    SKIP = "skip"          # Intentionally skipped (e.g., activation router said dormant)


class ErrorCategory(str, Enum):
    """What kind of failure."""

    INPUT = "input"            # Bad input data (validation, parsing, missing fields)
    PROCESSING = "processing"  # Logic failure (classification failed, plan invalid)
    EXTERNAL = "external"      # External dependency failed (MCP tool, API, network)
    RESOURCE = "resource"      # Out of budget, memory, or time
    POLICY = "policy"          # Blocked by guardrails, identity constraints, or ethics


class Severity(str, Enum):
    """How bad is the failure."""

    TRANSIENT = "transient"    # Retry will likely fix it (network blip, timeout)
    DEGRADED = "degraded"      # Partial functionality lost (can continue with reduced quality)
    FATAL = "fatal"            # Cannot continue — escalate or abort


# ============================================================================
# Core Supporting Models
# ============================================================================


class ModuleRef(BaseModel):
    """A pointer to a specific function in the kernel.

    Used to identify the origin of a Signal, the source of an error,
    or the target of a COMMAND signal. Every piece of data in the kernel
    carries a ModuleRef so the full provenance chain is always traceable.
    """

    tier: int = Field(..., ge=0, le=7, description="Tier number (0-7)")
    module: str = Field(..., min_length=1, description="Module name (e.g., 'classification')")
    function: str = Field(..., min_length=1, description="Function name (e.g., 'classify')")

    def __str__(self) -> str:
        return f"T{self.tier}.{self.module}.{self.function}"


# ============================================================================
# KernelError — Structured Failure
# ============================================================================


class KernelError(BaseModel):
    """Structured error for any kernel failure.

    Errors are first-class data, not exceptions. They flow through the pipeline
    carrying enough context for any module to decide: retry, escalate, or abort.

    Error codes follow the convention: T{tier}_{MODULE}_{REASON}
    Examples: T1_CLASSIFY_TIMEOUT, T4_TOOL_EXECUTION_FAILED, T6_HALLUCINATION_DETECTED
    """

    code: str = Field(..., description="Hierarchical: T{tier}_{MODULE}_{REASON}")
    category: ErrorCategory
    severity: Severity
    message: str = Field(..., min_length=1, description="Human-readable explanation")
    source: ModuleRef = Field(..., description="Which function failed")
    retry_eligible: bool = Field(default=False, description="Can the caller retry?")
    detail: dict[str, Any] = Field(default_factory=dict, description="Additional context")
    cause: KernelError | None = Field(default=None, description="Chained cause for wrapping")


# ============================================================================
# Signal — The Atomic Data Unit
# ============================================================================


class Signal(BaseModel):
    """The atomic, immutable data unit flowing through the kernel.

    Every piece of data flowing through the kernel is a Signal.
    Signals are immutable after creation — modules create new signals,
    they never mutate incoming ones. This guarantees traceability.

    Body conventions per kind:
        TEXT:    {"text": str}
        DATA:    {"data": Any, "schema": str, "count": int (if list)}
        FILE:    {"file_id": str, "file_type": str, "path": str | None}
        COMMAND: {"action": str, "target": {tier, module, function}, ...payload}
        STREAM:  {"chunk": str | bytes, "sequence": int, "final": bool}

    Standard tag keys:
        urgency, domain, complexity, confidence, grounding, source_type
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="sig_<ULID> — unique, time-sortable")
    kind: SignalKind = Field(..., description="What type of payload")
    body: dict[str, Any] = Field(..., description="The actual payload (typed per kind)")
    origin: ModuleRef = Field(..., description="Who created this signal")
    trace_id: str = Field(..., min_length=1, description="Correlation ID across the full pipeline")
    tags: dict[str, str] = Field(default_factory=dict, description="Flexible metadata")
    created_at: datetime = Field(..., description="UTC timestamp of creation")
    parent_id: str | None = Field(default=None, description="ID of the signal that triggered this one")


# ============================================================================
# Metrics — Execution Telemetry
# ============================================================================


class Metrics(BaseModel):
    """Execution telemetry attached to every Result.

    Every kernel function must report its resource consumption,
    enabling the Conscious Observer (T6) and Corporate Kernel (T7)
    to make informed resource allocation decisions.
    """

    duration_ms: float = Field(default=0.0, ge=0.0, description="Wall clock time")
    token_count: int = Field(default=0, ge=0, description="LLM tokens consumed (0 if no LLM call)")
    cache_hit: bool = Field(default=False, description="Was this served from cache?")
    module_ref: ModuleRef = Field(..., description="Which function produced this")


# ============================================================================
# Result — The Universal Function Return
# ============================================================================


class Result(BaseModel):
    """What every kernel function returns.

    No exceptions, no raw dicts, no bare strings. Every function in the
    kernel returns a Result. The pipeline engine (T4 OODA) reads the status
    to decide what to do next:

        OK      → consume output signals normally
        PARTIAL → process available signals, log the error, continue
        ERROR   → do NOT process signals, check retry_eligible, retry or escalate
        SKIP    → pass through, this module was intentionally dormant
    """

    status: ResultStatus = Field(..., description="How did it go?")
    signals: list[Signal] = Field(default_factory=list, description="Output signals")
    error: KernelError | None = Field(default=None, description="Populated if ERROR or PARTIAL")
    metrics: Metrics = Field(..., description="Always present — timing, tokens, cache")
