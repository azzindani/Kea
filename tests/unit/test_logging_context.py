"""
Tests for logging middleware.
"""

from unittest.mock import MagicMock

import pytest
from shared.logging.context import LogContext, reset_context, set_context
from shared.logging.middleware import (
    RequestIDMiddleware,
    RequestLoggingMiddleware,
)
from starlette.requests import Request
from starlette.responses import Response


class TestLogContext:
    """Tests for LogContext."""

    def test_log_context_creation(self):
        """Test creating log context."""
        ctx = LogContext(
            trace_id="trace_123",
            span_id="span_456",
            request_id="req_789",
        )
        assert ctx.trace_id == "trace_123"
        assert ctx.span_id == "span_456"
        assert ctx.request_id == "req_789"

    def test_set_and_reset_context(self):
        """Test setting and resetting context."""
        ctx = LogContext(
            trace_id="test_trace",
            span_id="test_span",
        )
        token = set_context(ctx)
        assert token is not None

        reset_context(token)


class TestRequestLoggingMiddleware:
    """Tests for RequestLoggingMiddleware."""

    @pytest.fixture
    def middleware(self):
        return RequestLoggingMiddleware(app=MagicMock())

    @pytest.mark.asyncio
    async def test_dispatch_adds_trace_headers(self, middleware):
        """Test that dispatch adds trace headers to response."""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.method = "GET"
        request.url.path = "/test"
        request.query_params = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        response = Response(content="OK", status_code=200)

        async def call_next(req):
            return response

        result = await middleware.dispatch(request, call_next)

        assert "X-Request-ID" in result.headers
        assert "X-Trace-ID" in result.headers

    @pytest.mark.asyncio
    async def test_dispatch_extracts_existing_trace_id(self, middleware):
        """Test that dispatch uses existing trace ID if present."""
        request = MagicMock(spec=Request)
        request.headers = {
            "X-Request-ID": "existing_req_id",
            "X-Trace-ID": "existing_trace_id",
        }
        request.method = "GET"
        request.url.path = "/test"
        request.query_params = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        response = Response(content="OK", status_code=200)

        async def call_next(req):
            return response

        result = await middleware.dispatch(request, call_next)

        assert result.headers["X-Request-ID"] == "existing_req_id"
        assert result.headers["X-Trace-ID"] == "existing_trace_id"


class TestRequestIDMiddleware:
    """Tests for RequestIDMiddleware."""

    @pytest.fixture
    def middleware(self):
        return RequestIDMiddleware(app=MagicMock())

    @pytest.mark.asyncio
    async def test_dispatch_generates_request_id(self, middleware):
        """Test that dispatch generates request ID."""
        request = MagicMock(spec=Request)
        request.headers = {}

        response = Response(content="OK", status_code=200)

        async def call_next(req):
            return response

        result = await middleware.dispatch(request, call_next)

        assert "X-Request-ID" in result.headers
        assert result.headers["X-Request-ID"].startswith("req-")

    @pytest.mark.asyncio
    async def test_dispatch_preserves_existing_request_id(self, middleware):
        """Test that dispatch preserves existing request ID."""
        request = MagicMock(spec=Request)
        request.headers = {"X-Request-ID": "my_req_id"}

        response = Response(content="OK", status_code=200)

        async def call_next(req):
            return response

        result = await middleware.dispatch(request, call_next)

        assert result.headers["X-Request-ID"] == "my_req_id"
