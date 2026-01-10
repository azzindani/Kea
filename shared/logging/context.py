"""
Logging Context Management.

Provides thread-safe context for trace_id, span_id, and request_id propagation.
"""

from __future__ import annotations

import contextvars
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LogContext:
    """
    Logging context with trace correlation.
    
    Contains:
    - trace_id: Distributed trace identifier
    - span_id: Current span identifier
    - request_id: Request correlation ID
    - extra: Additional context data
    """
    trace_id: str | None = None
    span_id: str | None = None
    request_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
    
    def with_span(self, span_id: str | None = None) -> "LogContext":
        """Create new context with a new span."""
        return LogContext(
            trace_id=self.trace_id,
            span_id=span_id or self._generate_id(),
            request_id=self.request_id,
            extra=self.extra.copy(),
        )
    
    def with_extra(self, **kwargs: Any) -> "LogContext":
        """Create new context with additional data."""
        new_extra = self.extra.copy()
        new_extra.update(kwargs)
        return LogContext(
            trace_id=self.trace_id,
            span_id=self.span_id,
            request_id=self.request_id,
            extra=new_extra,
        )
    
    @staticmethod
    def _generate_id() -> str:
        """Generate a random ID."""
        return uuid.uuid4().hex[:16]


# Context variable for thread-safe context storage
_context_var: contextvars.ContextVar[LogContext] = contextvars.ContextVar(
    "log_context",
    default=LogContext(),
)


def get_context() -> LogContext:
    """Get the current logging context."""
    return _context_var.get()


def set_context(context: LogContext) -> contextvars.Token[LogContext]:
    """
    Set the logging context.
    
    Args:
        context: New logging context
        
    Returns:
        Token for resetting context
    """
    return _context_var.set(context)


def reset_context(token: contextvars.Token[LogContext]) -> None:
    """Reset context to previous value using token."""
    _context_var.reset(token)


def new_trace_context(request_id: str | None = None) -> LogContext:
    """
    Create a new trace context.
    
    Args:
        request_id: Optional request ID (generated if not provided)
        
    Returns:
        New LogContext with fresh trace_id and span_id
    """
    return LogContext(
        trace_id=uuid.uuid4().hex,
        span_id=uuid.uuid4().hex[:16],
        request_id=request_id or f"req-{uuid.uuid4().hex[:8]}",
    )


class trace_context:
    """
    Context manager for trace context.
    
    Example:
        with trace_context(request_id="req-123") as ctx:
            logger.info("Processing", extra={"trace_id": ctx.trace_id})
    """
    
    def __init__(
        self,
        trace_id: str | None = None,
        span_id: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.context = LogContext(
            trace_id=trace_id or uuid.uuid4().hex,
            span_id=span_id or uuid.uuid4().hex[:16],
            request_id=request_id,
        )
        self._token: contextvars.Token[LogContext] | None = None
    
    def __enter__(self) -> LogContext:
        self._token = set_context(self.context)
        return self.context
    
    def __exit__(self, *args: Any) -> None:
        if self._token:
            reset_context(self._token)
