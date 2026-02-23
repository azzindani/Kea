"""
Kernel Standard I/O — Protocol Bridges.

Translates between the kernel's internal protocol (Signal/Result/KernelError)
and external protocols (MCP JSON-RPC 2.0, HTTP REST).

The kernel has two communication zones:
    Internal: In-process function calls using Signal/Result
    External: MCP ToolCallRequest/ToolResult, HTTP JobRequest/SuccessResponse/ProblemDetails

Bridge functions are the ONLY approved crossing points between these zones.
All bridges live in T0 (base foundation) and are stateless, pure functions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared.config import get_settings
from shared.mcp.protocol import (
    FileContent,
    ImageContent,
    JSONContent,
    JSONRPCError,
    JSONRPCNotification,
    JSONRPCVersion,
    MCPErrorCode,
    TextContent,
    ToolCallRequest,
    ToolResult,
)
from shared.schemas import (
    JobRequest,
    ProblemDetails,
    SuccessResponse,
)

from .errors import input_error
from .signals import (
    create_data_signal,
    create_file_signal,
    create_text_signal,
)
from .types import (
    ErrorCategory,
    KernelError,
    ModuleRef,
    Result,
    ResultStatus,
    Signal,
    SignalKind,
)


# ============================================================================
# Sentinel Origins for Bridge Boundaries
# ============================================================================

_GATEWAY_ORIGIN = ModuleRef(tier=0, module="gateway", function="bridge")
_MCP_ORIGIN = ModuleRef(tier=0, module="mcp", function="bridge")


# ============================================================================
# Category → HTTP Status Code Mapping
# ============================================================================

def _category_to_http_status(category: ErrorCategory) -> int:
    """Map ErrorCategory to HTTP status code from config."""
    settings = get_settings()
    mapping = {
        ErrorCategory.INPUT: settings.status_codes.bad_request,
        ErrorCategory.PROCESSING: settings.status_codes.internal_error,
        ErrorCategory.EXTERNAL: settings.status_codes.bad_gateway,
        ErrorCategory.RESOURCE: settings.status_codes.too_many_requests,
        ErrorCategory.POLICY: settings.status_codes.forbidden,
    }
    return mapping.get(category, settings.status_codes.internal_error)


# ============================================================================
# Category → JSON-RPC Error Code Mapping
# ============================================================================

def _category_to_jsonrpc_code(category: ErrorCategory) -> int:
    """Map ErrorCategory to JSON-RPC 2.0 error code."""
    mapping = {
        ErrorCategory.INPUT: MCPErrorCode.INVALID_PARAMS,
        ErrorCategory.PROCESSING: MCPErrorCode.INTERNAL_ERROR,
        ErrorCategory.EXTERNAL: MCPErrorCode.EXECUTION_ERROR,
        ErrorCategory.RESOURCE: MCPErrorCode.INTERNAL_ERROR,
        ErrorCategory.POLICY: MCPErrorCode.INVALID_REQUEST,
    }
    return mapping.get(category, MCPErrorCode.INTERNAL_ERROR)


# ============================================================================
# Signal → MCP (Outbound)
# ============================================================================


def signal_to_tool_call(signal: Signal) -> ToolCallRequest | KernelError:
    """Convert a DATA signal to an MCP ToolCallRequest.

    The signal body must contain:
        - "tool": str — the tool name to invoke
        - "args": dict — the tool arguments

    Args:
        signal: A Signal with kind=DATA containing tool invocation data.

    Returns:
        ToolCallRequest on success, or KernelError if the signal is malformed.
    """
    if signal.kind != SignalKind.DATA:
        return input_error(
            message=f"signal_to_tool_call requires kind=DATA, got kind={signal.kind.value}",
            source=_MCP_ORIGIN,
            detail={"signal_id": signal.id, "actual_kind": signal.kind.value},
        )

    tool_name = signal.body.get("tool")
    if not tool_name or not isinstance(tool_name, str):
        return input_error(
            message="Signal body missing required 'tool' key (str)",
            source=_MCP_ORIGIN,
            detail={"signal_id": signal.id, "body_keys": list(signal.body.keys())},
        )

    arguments = signal.body.get("args", {})
    if not isinstance(arguments, dict):
        return input_error(
            message="Signal body 'args' must be a dict",
            source=_MCP_ORIGIN,
            detail={"signal_id": signal.id, "args_type": type(arguments).__name__},
        )

    return ToolCallRequest(name=tool_name, arguments=arguments)


# ============================================================================
# MCP → Signal (Inbound)
# ============================================================================


def tool_result_to_signal(
    result: ToolResult,
    tool_name: str,
    trace_id: str,
) -> list[Signal]:
    """Convert an MCP ToolResult to one or more kernel Signals.

    A single ToolResult may contain multiple content types (text + JSON + files).
    This function splits them into separate typed signals:
        TextContent  → Signal(kind=TEXT)
        JSONContent  → Signal(kind=DATA)
        FileContent  → Signal(kind=FILE)
        ImageContent → Signal(kind=FILE)

    If the ToolResult has isError=True, returns a single TEXT signal
    containing the aggregated error text.

    All output signals share the same trace_id and carry the tool name in tags.

    Args:
        result: The MCP ToolResult from tool execution.
        tool_name: Name of the tool that produced this result.
        trace_id: Correlation ID for the full pipeline.

    Returns:
        List of 1-N signals split by content type.
    """
    origin = ModuleRef(tier=0, module="mcp", function=tool_name)
    tool_tags = {"source_type": "tool", "tool_name": tool_name}
    signals: list[Signal] = []

    # If the tool reported an error, aggregate text and return a single signal
    if result.isError:
        error_parts = [
            c.text for c in result.content
            if isinstance(c, TextContent)
        ]
        error_text = "\n".join(error_parts) if error_parts else f"Tool '{tool_name}' reported an error"
        signals.append(create_text_signal(
            text=error_text,
            origin=origin,
            trace_id=trace_id,
            tags={**tool_tags, "is_error": "true"},
        ))
        return signals

    # Split content types into separate signals
    for content in result.content:
        if isinstance(content, TextContent):
            signals.append(create_text_signal(
                text=content.text,
                origin=origin,
                trace_id=trace_id,
                tags=tool_tags,
            ))
        elif isinstance(content, JSONContent):
            schema = "list" if isinstance(content.data, list) else "dict"
            signals.append(create_data_signal(
                data=content.data,
                schema=schema,
                origin=origin,
                trace_id=trace_id,
                tags=tool_tags,
            ))
        elif isinstance(content, FileContent):
            signals.append(create_file_signal(
                file_id=content.path.rsplit("/", maxsplit=1)[-1] if "/" in content.path else content.path,
                file_type=content.mimeType,
                path=content.path,
                origin=origin,
                trace_id=trace_id,
            ))
        elif isinstance(content, ImageContent):
            signals.append(create_file_signal(
                file_id=f"image_{datetime.utcnow().timestamp()}",
                file_type=content.mimeType,
                path=None,
                origin=origin,
                trace_id=trace_id,
            ))

    # Guarantee at least one signal even for empty results
    if not signals:
        signals.append(create_text_signal(
            text=f"Tool '{tool_name}' returned empty result",
            origin=origin,
            trace_id=trace_id,
            tags=tool_tags,
        ))

    return signals


# ============================================================================
# Result → HTTP (Outbound)
# ============================================================================


def result_to_http_response(result: Result) -> SuccessResponse | ProblemDetails:
    """Convert a kernel Result to an HTTP response envelope.

    Mapping:
        OK / PARTIAL → SuccessResponse with signals serialized in data field
        ERROR        → ProblemDetails via error_to_problem_details()
        SKIP         → SuccessResponse with status="skipped"

    Args:
        result: The kernel Result to convert.

    Returns:
        SuccessResponse for OK/PARTIAL/SKIP, ProblemDetails for ERROR.
    """
    if result.status == ResultStatus.ERROR and result.error is not None:
        return error_to_problem_details(result.error)

    # OK, PARTIAL, or SKIP → success envelope
    serialized_signals = [sig.model_dump(mode="json") for sig in result.signals]
    data: dict[str, Any] = {
        "signals": serialized_signals,
        "signal_count": len(result.signals),
        "metrics": result.metrics.model_dump(mode="json"),
    }

    # Include partial error context if present
    if result.status == ResultStatus.PARTIAL and result.error is not None:
        data["warning"] = {
            "code": result.error.code,
            "message": result.error.message,
            "severity": result.error.severity.value,
        }

    status_label = result.status.value
    return SuccessResponse(
        status=status_label,
        message=f"Result: {status_label}",
        data=data,
    )


# ============================================================================
# HTTP → Signal (Inbound)
# ============================================================================


def http_request_to_signal(request: JobRequest, trace_id: str) -> Signal:
    """Convert an HTTP JobRequest to an input Signal.

    This is the entry point where external user requests enter the kernel
    pipeline. The query becomes a TEXT signal with job metadata as tags.

    Args:
        request: The incoming HTTP job request.
        trace_id: Correlation ID for the full pipeline.

    Returns:
        A TEXT signal with the user's query and job metadata tags.
    """
    tags: dict[str, str] = {
        "source_type": "user",
        "job_type": request.job_type.value,
        "depth": str(request.depth),
        "max_steps": str(request.max_steps),
    }
    if request.context_hints:
        tags["context_hints"] = ",".join(request.context_hints)

    return create_text_signal(
        text=request.query,
        origin=_GATEWAY_ORIGIN,
        trace_id=trace_id,
        tags=tags,
    )


# ============================================================================
# Signal → Notification Bus (Outbound)
# ============================================================================


def signal_to_notification(signal: Signal) -> JSONRPCNotification:
    """Convert a Signal to a fire-and-forget bus notification.

    Used for the internal artifact/event bus. Notifications have no response.

    Args:
        signal: Any kernel signal to broadcast.

    Returns:
        A JSON-RPC 2.0 Notification with the signal data.
    """
    return JSONRPCNotification(
        jsonrpc=JSONRPCVersion.V2,
        method="kernel/signal",
        params={
            "signal_id": signal.id,
            "kind": signal.kind.value,
            "origin": str(signal.origin),
            "trace_id": signal.trace_id,
            "tags": signal.tags,
            "body_keys": list(signal.body.keys()),
        },
    )


# ============================================================================
# KernelError → External Error Formats
# ============================================================================


def error_to_problem_details(error: KernelError) -> ProblemDetails:
    """Convert a KernelError to RFC 7807 ProblemDetails.

    Mapping:
        type   → "urn:kea:error:{code}" URI
        title  → category value
        status → HTTP status from category (INPUT→400, PROCESSING→500, etc.)
        detail → error message
        extensions → full error chain for debugging

    Args:
        error: The kernel error to convert.

    Returns:
        RFC 7807 compliant ProblemDetails for HTTP API responses.
    """
    extensions: dict[str, Any] = {
        "error_code": error.code,
        "severity": error.severity.value,
        "retry_eligible": error.retry_eligible,
        "source": str(error.source),
    }
    if error.detail:
        extensions["detail"] = error.detail
    if error.cause is not None:
        extensions["cause"] = {
            "code": error.cause.code,
            "message": error.cause.message,
            "source": str(error.cause.source),
        }

    return ProblemDetails(
        type=f"urn:kea:error:{error.code.lower()}",
        title=error.category.value,
        status=_category_to_http_status(error.category),
        detail=error.message,
        extensions=extensions,
    )


def error_to_jsonrpc_error(error: KernelError) -> JSONRPCError:
    """Convert a KernelError to JSON-RPC 2.0 error.

    Mapping:
        code    → JSON-RPC error code from category
        message → error message
        data    → error detail dict with code, severity, and cause chain

    Args:
        error: The kernel error to convert.

    Returns:
        JSON-RPC 2.0 error for MCP protocol responses.
    """
    data: dict[str, Any] = {
        "kernel_code": error.code,
        "category": error.category.value,
        "severity": error.severity.value,
        "retry_eligible": error.retry_eligible,
    }
    if error.detail:
        data["detail"] = error.detail
    if error.cause is not None:
        data["cause_code"] = error.cause.code
        data["cause_message"] = error.cause.message

    return JSONRPCError(
        code=_category_to_jsonrpc_code(error.category),
        message=error.message,
        data=data,
    )
