"""
Kernel Standard I/O Protocol.

The internal communication standard for the Kea Human Kernel. Every module
receives Signals, returns Results. Every failure is a KernelError — first-class
data, not an exception.

Usage::

    from redesign.tier_0.standard_io import (
        # Core types
        Signal, Result, KernelError, ModuleRef, Metrics,
        SignalKind, ResultStatus, ErrorCategory, Severity,
        # Signal factories
        create_signal, create_text_signal, create_data_signal,
        # Result factories
        ok, fail, partial, skip,
        # Error factories
        create_error, wrap_error, input_error,
        # Validation
        validate_signal, validate_result,
    )

    # Create a signal
    origin = ModuleRef(tier=1, module="classification", function="classify")
    signal = create_text_signal("Analyze Q3 revenue", origin, trace_id="abc123")

    # Return a result
    metrics = Metrics(duration_ms=42.0, module_ref=origin)
    result = ok(signals=[signal], metrics=metrics)

    # Handle errors
    error = input_error("Missing required field", source=origin)
    result = fail(error=error, metrics=metrics)

Protocol Bridges (translate between internal/external protocols)::

    from redesign.tier_0.standard_io import (
        signal_to_tool_call, tool_result_to_signal,
        result_to_http_response, http_request_to_signal,
    )
"""

from __future__ import annotations

# Core types and enumerations
from .types import (
    ErrorCategory,
    KernelError,
    Metrics,
    ModuleRef,
    Result,
    ResultStatus,
    Severity,
    Signal,
    SignalKind,
)

# Signal factory functions
from .signals import (
    create_command_signal,
    create_data_signal,
    create_error_signal,
    create_file_signal,
    create_signal,
    create_text_signal,
)

# Result factory functions
from .results import (
    fail,
    ok,
    partial,
    skip,
)

# Error factory functions
from .errors import (
    create_error,
    external_error,
    input_error,
    policy_error,
    processing_error,
    resource_error,
    wrap_error,
)

# Protocol bridges
from .bridges import (
    error_to_jsonrpc_error,
    error_to_problem_details,
    http_request_to_signal,
    result_to_http_response,
    signal_to_notification,
    signal_to_tool_call,
    tool_result_to_signal,
)

# Validation functions
from .validation import (
    validate_result,
    validate_signal,
)

__all__ = [
    # Enumerations
    "SignalKind",
    "ResultStatus",
    "ErrorCategory",
    "Severity",
    # Core types
    "ModuleRef",
    "Signal",
    "KernelError",
    "Metrics",
    "Result",
    # Signal factories
    "create_signal",
    "create_text_signal",
    "create_data_signal",
    "create_file_signal",
    "create_command_signal",
    "create_error_signal",
    # Result factories
    "ok",
    "partial",
    "fail",
    "skip",
    # Error factories
    "create_error",
    "input_error",
    "processing_error",
    "external_error",
    "resource_error",
    "policy_error",
    "wrap_error",
    # Protocol bridges
    "signal_to_tool_call",
    "tool_result_to_signal",
    "result_to_http_response",
    "http_request_to_signal",
    "signal_to_notification",
    "error_to_problem_details",
    "error_to_jsonrpc_error",
    # Validation
    "validate_signal",
    "validate_result",
]
