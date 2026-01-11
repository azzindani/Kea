"""
Unit Tests: Logging Context and Decorators.

Tests for shared/logging/context.py, decorators.py, structured.py
"""

import pytest


class TestLogContext:
    """Tests for log context management."""
    
    def test_set_and_get_context(self):
        """Set and retrieve context."""
        from shared.logging.context import set_log_context, get_log_context, clear_log_context
        
        clear_log_context()
        
        set_log_context(trace_id="trace-123", job_id="job-456")
        
        ctx = get_log_context()
        
        assert ctx["trace_id"] == "trace-123"
        assert ctx["job_id"] == "job-456"
    
    def test_clear_context(self):
        """Clear log context."""
        from shared.logging.context import set_log_context, get_log_context, clear_log_context
        
        set_log_context(key="value")
        clear_log_context()
        
        ctx = get_log_context()
        
        assert "key" not in ctx
    
    def test_context_manager(self):
        """Use context manager."""
        from shared.logging.context import log_context, get_log_context
        
        with log_context(request_id="req-123"):
            ctx = get_log_context()
            assert ctx.get("request_id") == "req-123"


class TestLogDecorators:
    """Tests for logging decorators."""
    
    def test_log_execution_sync(self):
        """Decorator on sync function."""
        from shared.logging.decorators import log_execution
        
        @log_execution
        def add(a, b):
            return a + b
        
        result = add(3, 4)
        
        assert result == 7
    
    @pytest.mark.asyncio
    async def test_log_execution_async(self):
        """Decorator on async function."""
        from shared.logging.decorators import log_execution
        
        @log_execution
        async def multiply(a, b):
            return a * b
        
        result = await multiply(3, 4)
        
        assert result == 12
    
    def test_log_execution_with_exception(self):
        """Decorator handles exceptions."""
        from shared.logging.decorators import log_execution
        
        @log_execution
        def fail():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            fail()


class TestStructuredLogger:
    """Tests for structured logging."""
    
    def test_create_logger(self):
        """Create structured logger."""
        from shared.logging.structured import get_structured_logger
        
        logger = get_structured_logger("test_module")
        
        assert logger is not None
    
    def test_log_with_context(self):
        """Log with extra context."""
        from shared.logging.structured import get_structured_logger
        
        logger = get_structured_logger("test")
        
        # Should not raise
        logger.info("Test message", extra={"key": "value"})
    
    def test_log_levels(self):
        """All log levels work."""
        from shared.logging.structured import get_structured_logger
        
        logger = get_structured_logger("levels")
        
        logger.debug("debug")
        logger.info("info")
        logger.warning("warning")
        logger.error("error")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
