"""
Request Tracing.

Lightweight request tracing for debugging and observability.
Uses trace IDs and spans without full OpenTelemetry dependency.
"""

from __future__ import annotations

import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from shared.logging import get_logger


logger = get_logger(__name__)


# Context variable for current trace
_current_trace: ContextVar["Trace"] = ContextVar("current_trace", default=None)


@dataclass
class Span:
    """A span in a trace."""
    span_id: str
    name: str
    start_time: float
    end_time: float | None = None
    parent_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict] = field(default_factory=list)
    status: str = "ok"
    
    @property
    def duration_ms(self) -> float:
        if self.end_time is None:
            return (time.time() - self.start_time) * 1000
        return (self.end_time - self.start_time) * 1000
    
    def add_event(self, name: str, attributes: dict = None):
        """Add event to span."""
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })
    
    def set_attribute(self, key: str, value: Any):
        """Set span attribute."""
        self.attributes[key] = value
    
    def set_status(self, status: str, message: str = None):
        """Set span status."""
        self.status = status
        if message:
            self.attributes["status_message"] = message
    
    def end(self):
        """End the span."""
        self.end_time = time.time()
    
    def to_dict(self) -> dict:
        return {
            "span_id": self.span_id,
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "parent_id": self.parent_id,
            "attributes": self.attributes,
            "events": self.events,
            "status": self.status,
        }


@dataclass
class Trace:
    """A distributed trace."""
    trace_id: str
    service_name: str = "project"
    spans: list[Span] = field(default_factory=list)
    _current_span: Span | None = None
    
    @classmethod
    def create(cls, service_name: str = "project") -> "Trace":
        """Create new trace."""
        trace = cls(
            trace_id=str(uuid.uuid4()),
            service_name=service_name,
        )
        _current_trace.set(trace)
        return trace
    
    @classmethod
    def get_current(cls) -> "Trace | None":
        """Get current trace."""
        return _current_trace.get()
    
    def start_span(self, name: str, attributes: dict = None) -> Span:
        """Start a new span."""
        span = Span(
            span_id=str(uuid.uuid4())[:8],
            name=name,
            start_time=time.time(),
            parent_id=self._current_span.span_id if self._current_span else None,
            attributes=attributes or {},
        )
        self.spans.append(span)
        self._current_span = span
        return span
    
    def end_span(self):
        """End current span."""
        if self._current_span:
            self._current_span.end()
            # Find parent
            if self._current_span.parent_id:
                for span in self.spans:
                    if span.span_id == self._current_span.parent_id:
                        self._current_span = span
                        return
            self._current_span = None
    
    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "service_name": self.service_name,
            "spans": [s.to_dict() for s in self.spans],
        }


class TracingMiddleware(BaseHTTPMiddleware):
    """
    Request tracing middleware.
    
    Adds trace ID header and logs request spans.
    """
    
    def __init__(self, app, service_name: str = "project"):
        super().__init__(app)
        self.service_name = service_name
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get or create trace ID
        trace_id = request.headers.get("X-Trace-ID")
        if not trace_id:
            trace_id = str(uuid.uuid4())
        
        # Create trace
        trace = Trace(trace_id=trace_id, service_name=self.service_name)
        _current_trace.set(trace)
        
        # Start request span
        span = trace.start_span(
            f"{request.method} {request.url.path}",
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
                "http.client_ip": request.client.host if request.client else None,
            },
        )
        
        try:
            response = await call_next(request)
            
            span.set_attribute("http.status_code", response.status_code)
            if response.status_code >= 400:
                span.set_status("error")
            
            # Add trace ID to response
            response.headers["X-Trace-ID"] = trace_id
            
            return response
            
        except Exception as e:
            span.set_status("error", str(e))
            raise
            
        finally:
            span.end()
            
            # Log trace summary
            logger.debug(
                f"Trace {trace_id}: {span.name} - {span.duration_ms:.2f}ms",
                extra={"trace": trace.to_dict()},
            )


# ============================================================================
# Decorator for tracing functions
# ============================================================================

def trace_function(name: str = None):
    """Decorator to trace a function."""
    def decorator(func: Callable) -> Callable:
        span_name = name or func.__name__
        
        async def async_wrapper(*args, **kwargs):
            trace = Trace.get_current()
            if trace:
                span = trace.start_span(span_name)
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.set_status("error", str(e))
                    raise
                finally:
                    span.end()
            else:
                return await func(*args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            trace = Trace.get_current()
            if trace:
                span = trace.start_span(span_name)
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    span.set_status("error", str(e))
                    raise
                finally:
                    span.end()
            else:
                return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# ============================================================================
# Helpers
# ============================================================================

def get_trace_id() -> str | None:
    """Get current trace ID."""
    trace = Trace.get_current()
    return trace.trace_id if trace else None


def add_span_attribute(key: str, value: Any):
    """Add attribute to current span."""
    trace = Trace.get_current()
    if trace and trace._current_span:
        trace._current_span.set_attribute(key, value)


def add_span_event(name: str, attributes: dict = None):
    """Add event to current span."""
    trace = Trace.get_current()
    if trace and trace._current_span:
        trace._current_span.add_event(name, attributes)
