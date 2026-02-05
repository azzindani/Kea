"""
FastAPI Logging Middleware.

Provides request/response logging with trace correlation.
"""

from __future__ import annotations

import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from shared.logging.structured import get_logger
from shared.logging.context import LogContext, set_context, reset_context
from shared.logging.metrics import record_api_request


logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests with trace correlation.
    
    Features:
    - Generates/extracts request_id and trace_id
    - Logs request start and completion
    - Records Prometheus metrics
    - Propagates context to handlers
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract or generate trace context
        request_id = request.headers.get("X-Request-ID", f"req-{uuid.uuid4().hex[:8]}")
        trace_id = request.headers.get("X-Trace-ID", uuid.uuid4().hex)
        span_id = uuid.uuid4().hex[:16]
        
        # Set logging context
        context = LogContext(
            trace_id=trace_id,
            span_id=span_id,
            request_id=request_id,
        )
        token = set_context(context)
        
        # Log request start
        start_log_data = {
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "client_ip": request.client.host if request.client else None,
        }
        
        # Verbose Mode: Log Body
        import os
        if os.getenv("KEA_LOG_NO_TRUNCATE") == "1":
            try:
                # Read and reset body
                body_bytes = await request.body()
                start_log_data["body"] = body_bytes.decode(errors="replace")
                
                # Re-inject body for downstream
                async def receive():
                    return {"type": "http.request", "body": body_bytes, "more_body": False}
                request._receive = receive
            except Exception:
                start_log_data["body"] = "<error reading body>"

        logger.info("Request started", extra=start_log_data)
        
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            duration = time.perf_counter() - start_time
            
            # Log request completion
            logger.info(
                "Request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                }
            )
            
            # Record metrics
            record_api_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                duration=duration,
            )
            
            # Add trace headers to response
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Trace-ID"] = trace_id
            
            return response
            
        except Exception as e:
            duration = time.perf_counter() - start_time
            
            logger.error(
                "Request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "duration_ms": round(duration * 1000, 2),
                },
                exc_info=True,
            )
            
            # Record error metrics
            record_api_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=500,
                duration=duration,
            )
            
            raise
            
        finally:
            reset_context(token)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Simple middleware that ensures every request has an ID.
    
    Use this for lightweight request tracking without full logging.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", f"req-{uuid.uuid4().hex[:8]}")
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response
