"""
Kernel Standard I/O — Result Factory Functions.

Every kernel function returns a Result. These factories enforce the correct
status-to-content mapping:

    ok()      → OK status, signals populated, no error
    partial() → PARTIAL status, some signals + error context
    fail()    → ERROR status, no signals, error populated
    skip()    → SKIP status, empty signals, no error
"""

from __future__ import annotations

from .types import KernelError, Metrics, Result, ResultStatus, Signal


def ok(signals: list[Signal], metrics: Metrics) -> Result:
    """Successful result — all output signals present, no error."""
    return Result(
        status=ResultStatus.OK,
        signals=signals,
        metrics=metrics,
    )


def partial(signals: list[Signal], error: KernelError, metrics: Metrics) -> Result:
    """Partial success — some signals available, with error context.

    Used when a function produced useful partial output but encountered
    a non-fatal error during processing. Downstream modules should process
    the available signals and log the error.
    """
    return Result(
        status=ResultStatus.PARTIAL,
        signals=signals,
        error=error,
        metrics=metrics,
    )


def fail(error: KernelError, metrics: Metrics) -> Result:
    """Failed result — no output signals, error populated.

    Downstream modules should NOT process signals from a failed result.
    Instead, check error.retry_eligible and error.severity to decide
    whether to retry, escalate, or abort.
    """
    return Result(
        status=ResultStatus.ERROR,
        error=error,
        metrics=metrics,
    )


def skip(reason: str, metrics: Metrics) -> Result:
    """Intentionally skipped — module was dormant.

    Used when a module is intentionally not activated (e.g., T6 Activation
    Router determined this signal doesn't need this module). The reason
    parameter documents why the skip occurred for tracing purposes.

    Args:
        reason: Human-readable explanation of why the module was skipped.
        metrics: Execution telemetry (duration will typically be near-zero).

    Returns:
        A Result with SKIP status and empty signals.
    """
    return Result(
        status=ResultStatus.SKIP,
        signals=[],
        metrics=metrics,
    )
