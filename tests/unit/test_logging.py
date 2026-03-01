"""
Unit Tests: Logging.

Tests for shared/logging/*.py
"""

import pytest


class TestStructuredLogging:
    """Tests for structured logging."""

    def test_get_logger(self):
        """Get logger by name."""
        from shared.logging.main import get_logger

        logger = get_logger("test_module")

        assert logger is not None
        assert "test_module" in logger.name

    def test_log_levels(self):
        """Logger supports all levels."""
        from shared.logging.main import get_logger

        logger = get_logger("test_levels")

        # Should not raise
        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")


class TestLogConfig:
    """Tests for log configuration."""

    def test_create_config(self):
        """Create log config."""
        from shared.logging.main import LogConfig

        config = LogConfig(
            level="DEBUG",
            format="json",
            service_name="test_service",
        )

        assert config.level == "DEBUG"
        assert config.service_name == "test_service"

    def test_setup_logging(self):
        """Setup logging from config."""
        from shared.logging.main import LogConfig, setup_logging

        config = LogConfig(
            level="INFO",
            format="json",
            service_name="test",
        )

        # Should not raise
        setup_logging(config)


class TestLogContext:
    """Tests for log context."""

    def test_set_context(self):
        """Set log context using LogContext object."""
        from shared.logging.context import get_context, set_context

        from shared.logging.main import LogContext

        ctx = LogContext(trace_id="trace-123", request_id="req-456")
        set_context(ctx)

        current = get_context()

        assert current.trace_id == "trace-123"


class TestLogDecorator:
    """Tests for log execution decorator."""

    def test_decorator_sync(self):
        """Decorator works on sync functions (with parentheses)."""
        from shared.logging.main import log_execution

        @log_execution()  # Note: requires parentheses - it's a decorator factory
        def test_func(x, y):
            return x + y

        result = test_func(1, 2)

        assert result == 3

    @pytest.mark.asyncio
    async def test_decorator_async(self):
        """Decorator works on async functions."""
        from shared.logging.main import log_execution

        @log_execution()  # Note: requires parentheses
        async def test_async_func(x):
            return x * 2

        result = await test_async_func(5)

        assert result == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
