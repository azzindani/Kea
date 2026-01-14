"""
Tests for Logging Decorators and Middleware.
"""

import pytest


class TestLoggingDecorators:
    """Tests for logging decorators."""
    
    def test_import_decorators(self):
        """Test decorators module imports."""
        from shared.logging.decorators import (
            log_function,
            log_async_function,
            timed,
            trace,
        )
        
        assert log_function is not None
        print("\n✅ Decorator imports work")
    
    def test_log_function_decorator(self):
        """Test function logging decorator."""
        from shared.logging.decorators import log_function
        
        @log_function
        def test_func(x, y):
            return x + y
        
        result = test_func(1, 2)
        
        assert result == 3
        print("\n✅ log_function decorator works")
    
    @pytest.mark.asyncio
    async def test_log_async_function_decorator(self):
        """Test async function logging decorator."""
        from shared.logging.decorators import log_async_function
        
        @log_async_function
        async def async_test_func(x):
            return x * 2
        
        result = await async_test_func(5)
        
        assert result == 10
        print("\n✅ log_async_function decorator works")
    
    def test_timed_decorator(self):
        """Test timing decorator."""
        from shared.logging.decorators import timed
        import time
        
        @timed
        def slow_func():
            time.sleep(0.01)
            return "done"
        
        result = slow_func()
        
        assert result == "done"
        print("\n✅ timed decorator works")
    
    def test_trace_decorator(self):
        """Test tracing decorator."""
        from shared.logging.decorators import trace
        
        @trace(name="test_operation")
        def traced_func():
            return "traced"
        
        result = traced_func()
        
        assert result == "traced"
        print("\n✅ trace decorator works")


class TestLoggingContext:
    """Tests for logging context."""
    
    def test_import_context(self):
        """Test context module imports."""
        from shared.logging.context import (
            LogContext,
            get_context,
            set_context,
        )
        
        assert LogContext is not None
        print("\n✅ Context imports work")
    
    def test_create_context(self):
        """Test creating log context."""
        from shared.logging.context import LogContext
        
        ctx = LogContext(
            request_id="req_123",
            user_id="user_456",
            operation="research",
        )
        
        assert ctx.request_id == "req_123"
        print("\n✅ LogContext created")
    
    def test_context_propagation(self):
        """Test context propagation."""
        from shared.logging.context import set_context, get_context
        
        set_context("session_id", "sess_789")
        
        value = get_context("session_id")
        
        assert value == "sess_789"
        print("\n✅ Context propagation works")


class TestLoggingMiddleware:
    """Tests for logging middleware."""
    
    def test_import_middleware(self):
        """Test middleware module imports."""
        from shared.logging.middleware import (
            LoggingMiddleware,
            RequestLoggingMiddleware,
        )
        
        assert LoggingMiddleware is not None
        print("\n✅ Middleware imports work")
    
    def test_create_middleware(self):
        """Test middleware creation."""
        from shared.logging.middleware import LoggingMiddleware
        
        middleware = LoggingMiddleware()
        
        assert middleware is not None
        print("\n✅ Middleware created")


class TestMCPMiddleware:
    """Tests for MCP-specific logging middleware."""
    
    def test_import_mcp_middleware(self):
        """Test MCP middleware imports."""
        from shared.logging.mcp_middleware import (
            MCPLoggingMiddleware,
            log_mcp_request,
        )
        
        assert MCPLoggingMiddleware is not None or log_mcp_request is not None
        print("\n✅ MCP middleware imports work")
    
    def test_log_tool_call(self):
        """Test logging MCP tool calls."""
        from shared.logging.mcp_middleware import MCPLoggingMiddleware
        
        middleware = MCPLoggingMiddleware()
        
        # Test logging a tool call
        middleware.log_tool_call(
            tool_name="web_search",
            arguments={"query": "Tesla"},
            server="search_server",
        )
        
        print("\n✅ Tool call logged")


class TestStructuredLogging:
    """Tests for structured logging."""
    
    def test_import_structured(self):
        """Test structured logging imports."""
        from shared.logging.structured import (
            StructuredLogger,
            LogEntry,
        )
        
        assert StructuredLogger is not None
        print("\n✅ Structured logging imports work")
    
    def test_create_structured_logger(self):
        """Test structured logger creation."""
        from shared.logging.structured import StructuredLogger
        
        logger = StructuredLogger("test_module")
        
        assert logger is not None
        print("\n✅ StructuredLogger created")
    
    def test_log_with_metadata(self):
        """Test logging with metadata."""
        from shared.logging.structured import StructuredLogger
        
        logger = StructuredLogger("test")
        
        logger.info(
            "Operation completed",
            extra={
                "duration_ms": 150,
                "items_processed": 100,
            }
        )
        
        print("\n✅ Metadata logging works")


class TestMetrics:
    """Tests for logging metrics."""
    
    def test_import_metrics(self):
        """Test metrics module imports."""
        from shared.logging.metrics import (
            counter,
            gauge,
            histogram,
            record_metric,
        )
        
        assert record_metric is not None
        print("\n✅ Metrics imports work")
    
    def test_record_counter(self):
        """Test recording counter metric."""
        from shared.logging.metrics import counter
        
        counter("api_requests_total", 1, labels={"endpoint": "/research"})
        
        print("\n✅ Counter recorded")
    
    def test_record_histogram(self):
        """Test recording histogram metric."""
        from shared.logging.metrics import histogram
        
        histogram("request_duration_seconds", 0.5, labels={"method": "GET"})
        
        print("\n✅ Histogram recorded")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
