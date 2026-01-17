"""
Tests for logging decorators and extended logging.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestLoggingDecorators:
    """Tests for log_execution decorator."""
    
    def test_import_decorators(self):
        """Test that decorators can be imported."""
        from shared.logging.decorators import log_execution
        assert log_execution is not None
    
    @pytest.mark.asyncio
    async def test_log_execution_async(self):
        """Test log_execution with async function."""
        from shared.logging.decorators import log_execution
        
        @log_execution(log_timing=True)
        async def async_func():
            return "result"
        
        result = await async_func()
        assert result == "result"
    
    def test_log_execution_sync(self):
        """Test log_execution with sync function."""
        from shared.logging.decorators import log_execution
        
        @log_execution(log_timing=True)
        def sync_func():
            return "sync result"
        
        result = sync_func()
        assert result == "sync result"
    
    @pytest.mark.asyncio
    async def test_log_execution_with_args(self):
        """Test log_execution logs arguments."""
        from shared.logging.decorators import log_execution
        
        @log_execution(log_args=True, log_result=True)
        async def func_with_args(x, y):
            return x + y
        
        result = await func_with_args(1, 2)
        assert result == 3


class TestLoggingContext:
    """Tests for LogContext."""
    
    def test_import_context(self):
        """Test that context can be imported."""
        from shared.logging.context import LogContext, set_context, get_context
        assert LogContext is not None
        assert set_context is not None
    
    def test_create_context(self):
        """Test creating log context."""
        from shared.logging.context import LogContext
        
        ctx = LogContext(
            trace_id="trace_123",
            span_id="span_456",
            request_id="req_789",
        )
        
        assert ctx.trace_id == "trace_123"
        assert ctx.span_id == "span_456"
        assert ctx.request_id == "req_789"


class TestLoggingMiddleware:
    """Tests for logging middleware."""
    
    def test_import_middleware(self):
        """Test that middleware can be imported."""
        from shared.logging.middleware import (
            RequestLoggingMiddleware,
            RequestIDMiddleware,
        )
        assert RequestLoggingMiddleware is not None
        assert RequestIDMiddleware is not None


class TestStructuredLogging:
    """Tests for structured logging."""
    
    def test_import_structured(self):
        """Test that structured logging can be imported."""
        from shared.logging.structured import get_logger
        assert get_logger is not None
    
    def test_create_logger(self):
        """Test creating structured logger."""
        from shared.logging.structured import get_logger
        
        logger = get_logger("test.module")
        assert logger is not None


class TestMetrics:
    """Tests for metrics module."""
    
    def test_import_metrics(self):
        """Test that metrics can be imported."""
        from shared.logging.metrics import record_api_request
        assert record_api_request is not None
    
    def test_record_api_request(self):
        """Test recording API request metric."""
        from shared.logging.metrics import record_api_request
        
        # Should not raise
        record_api_request(
            method="GET",
            endpoint="/api/test",
            status_code=200,
            duration=0.1,
        )
