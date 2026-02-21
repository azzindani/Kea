"""
Unit Tests: Logging Detailed.

Additional tests for shared/logging/*.py
"""

import pytest


class TestLogContext:
    """Tests for log context management."""
    
    def test_set_and_get_context(self):
        """Set and get context."""
        from shared.logging.context import LogContext, set_context, get_context
        
        ctx = LogContext(trace_id="trace-abc", request_id="req-123")
        set_context(ctx)
        
        current = get_context()
        
        assert current.trace_id == "trace-abc"
        assert current.request_id == "req-123"
    
    def test_clear_context(self):
        """Reset context to default."""
        from shared.logging.context import LogContext, set_context, get_context, reset_context
        
        ctx = LogContext(trace_id="trace-123")
        token = set_context(ctx)
        
        # Reset to previous
        reset_context(token)
        
        current = get_context()
        # After reset, should be back to default (empty context)
        assert current is not None
    
    def test_context_manager(self):
        """Use trace_context as context manager."""
        from shared.logging.context import trace_context
        
        with trace_context(request_id="req-123") as ctx:
            assert ctx.request_id == "req-123"


class TestLogDecorators:
    """Tests for log decorators."""
    
    def test_log_execution_sync(self):
        """Decorator on sync function."""
        from shared.logging.main import log_execution
        
        @log_execution()
        def add(a, b):
            return a + b
        
        result = add(3, 4)
        assert result == 7
    
    @pytest.mark.asyncio
    async def test_log_execution_async(self):
        """Decorator on async function."""
        from shared.logging.main import log_execution
        
        @log_execution()
        async def multiply(a, b):
            return a * b
        
        result = await multiply(3, 4)
        assert result == 12
    
    def test_log_execution_with_exception(self):
        """Decorator logs exceptions."""
        from shared.logging.main import log_execution
        
        @log_execution()
        def fail():
            raise ValueError("test error")
        
        with pytest.raises(ValueError):
            fail()


class TestStructuredLogger:
    """Tests for structured logger."""
    
    def test_create_logger(self):
        """Create structured logger using get_logger."""
        from shared.logging.main import get_logger
        
        logger = get_logger("test.structured")
        
        assert logger is not None
    
    def test_log_with_context(self):
        """Log with extra context."""
        from shared.logging.main import get_logger
        
        logger = get_logger("test.context")
        
        # Should not raise
        logger.info("message", extra={"key": "value"})
    
    def test_log_levels(self):
        """All log levels work."""
        from shared.logging.main import get_logger
        
        logger = get_logger("test.levels")
        
        logger.debug("debug")
        logger.info("info")
        logger.warning("warn")
        logger.error("error")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
