"""
Kernel Standard I/O — Error Factory Functions.

All KernelError creation flows through these factories. The universal
create_error() validates the error code convention. Convenience factories
(input_error, processing_error, etc.) generate well-formed codes automatically.

Error Code Convention: T{tier}_{MODULE}_{REASON}
    Examples:
        T0_VALIDATION_SCHEMA_MISMATCH
        T1_CLASSIFY_TIMEOUT
        T4_TOOL_EXECUTION_FAILED
        T6_HALLUCINATION_DETECTED
"""

from __future__ import annotations

import re
from typing import Any

from .types import ErrorCategory, KernelError, ModuleRef, Severity


# Error code must match: T<digit>_<UPPER_WORD>_<UPPER_WORD(S)>
_ERROR_CODE_PATTERN = re.compile(r"^T\d+_[A-Z][A-Z0-9]*(?:_[A-Z][A-Z0-9]*)+$")


# ============================================================================
# Universal Factory
# ============================================================================


def create_error(
    code: str,
    category: ErrorCategory,
    severity: Severity,
    message: str,
    source: ModuleRef,
    retry: bool = False,
    detail: dict[str, Any] | None = None,
    cause: KernelError | None = None,
) -> KernelError:
    """Universal error factory. Validates the error code convention.

    Args:
        code: Must follow T{tier}_{MODULE}_{REASON} (e.g., "T1_CLASSIFY_TIMEOUT").
        category: What kind of failure (INPUT, PROCESSING, EXTERNAL, RESOURCE, POLICY).
        severity: How bad (TRANSIENT, DEGRADED, FATAL).
        message: Human-readable explanation.
        source: Which function failed.
        retry: Whether the caller can retry.
        detail: Additional context (stack trace, raw input, etc.).
        cause: Chained inner error for wrapping.

    Returns:
        A new KernelError.

    Raises:
        ValueError: If the error code doesn't match the convention.
    """
    if not _ERROR_CODE_PATTERN.match(code):
        raise ValueError(
            f"Error code '{code}' does not match T{{tier}}_{{MODULE}}_{{REASON}} convention. "
            f"Expected pattern: T<digit>_<UPPER>_<UPPER> (e.g., 'T1_CLASSIFY_TIMEOUT')"
        )

    return KernelError(
        code=code,
        category=category,
        severity=severity,
        message=message,
        source=source,
        retry_eligible=retry,
        detail=detail or {},
        cause=cause,
    )


# ============================================================================
# Convenience Factories
# ============================================================================


def input_error(
    message: str,
    source: ModuleRef,
    detail: dict[str, Any] | None = None,
) -> KernelError:
    """Convenience: INPUT category, TRANSIENT severity, not retryable.

    For bad input data — validation failures, parsing errors, missing fields.
    """
    code = f"T{source.tier}_{source.module.upper()}_INPUT_INVALID"
    return create_error(
        code=code,
        category=ErrorCategory.INPUT,
        severity=Severity.TRANSIENT,
        message=message,
        source=source,
        retry=False,
        detail=detail,
    )


def processing_error(
    message: str,
    source: ModuleRef,
    detail: dict[str, Any] | None = None,
    cause: KernelError | None = None,
) -> KernelError:
    """Convenience: PROCESSING category, DEGRADED severity.

    For logic failures — classification failed, plan invalid, etc.
    """
    code = f"T{source.tier}_{source.module.upper()}_PROCESSING_FAILED"
    return create_error(
        code=code,
        category=ErrorCategory.PROCESSING,
        severity=Severity.DEGRADED,
        message=message,
        source=source,
        retry=False,
        detail=detail,
        cause=cause,
    )


def external_error(
    message: str,
    source: ModuleRef,
    retry: bool = True,
    detail: dict[str, Any] | None = None,
) -> KernelError:
    """Convenience: EXTERNAL category, TRANSIENT severity.

    For external dependency failures — MCP tool errors, API timeouts, network issues.
    Defaults to retry_eligible=True since external failures are often transient.
    """
    code = f"T{source.tier}_{source.module.upper()}_EXTERNAL_FAILED"
    return create_error(
        code=code,
        category=ErrorCategory.EXTERNAL,
        severity=Severity.TRANSIENT,
        message=message,
        source=source,
        retry=retry,
        detail=detail,
    )


def resource_error(
    message: str,
    source: ModuleRef,
    detail: dict[str, Any] | None = None,
) -> KernelError:
    """Convenience: RESOURCE category, FATAL severity.

    For budget exhaustion, memory pressure, time limits exceeded.
    """
    code = f"T{source.tier}_{source.module.upper()}_RESOURCE_EXHAUSTED"
    return create_error(
        code=code,
        category=ErrorCategory.RESOURCE,
        severity=Severity.FATAL,
        message=message,
        source=source,
        retry=False,
        detail=detail,
    )


def policy_error(
    message: str,
    source: ModuleRef,
    detail: dict[str, Any] | None = None,
) -> KernelError:
    """Convenience: POLICY category, FATAL severity.

    For guardrail violations, identity constraint breaches, ethical blocks.
    """
    code = f"T{source.tier}_{source.module.upper()}_POLICY_VIOLATION"
    return create_error(
        code=code,
        category=ErrorCategory.POLICY,
        severity=Severity.FATAL,
        message=message,
        source=source,
        retry=False,
        detail=detail,
    )


# ============================================================================
# Error Wrapping
# ============================================================================


def wrap_error(
    outer_code: str,
    inner: KernelError,
    source: ModuleRef,
    message: str | None = None,
) -> KernelError:
    """Wrap a lower-tier error with upper-tier context.

    Preserves the inner error as cause, inherits category and severity
    from the inner error (promoting to FATAL if the outer tier cannot
    recover), and generates a contextual message.

    This is the standard pattern for error propagation across tier boundaries:
        T1 error → T4 wraps it → T5 wraps it → T6 evaluates it

    Args:
        outer_code: The wrapping tier's error code (e.g., "T4_OODA_INNER_FAILURE").
        inner: The original error from a lower tier.
        source: The wrapping function's ModuleRef.
        message: Optional override message. If None, auto-generates from context.

    Returns:
        A new KernelError with the inner error chained as cause.
    """
    auto_message = (
        message
        or f"{source} encountered {inner.code}: {inner.message}"
    )

    return create_error(
        code=outer_code,
        category=inner.category,
        severity=inner.severity,
        message=auto_message,
        source=source,
        retry=inner.retry_eligible,
        detail={"wrapped_code": inner.code, "wrapped_source": str(inner.source)},
        cause=inner,
    )
