# Shared Logging Package
"""
Structured logging with OpenTelemetry integration.

Components:
- structured: JSON formatter and logger setup
- context: Log context management (trace/span IDs)
- decorators: @log_execution decorator
- metrics: Prometheus metrics
- middleware: FastAPI and MCP middleware
"""

from shared.logging.structured import (
    setup_logging,
    get_logger,
    LogConfig,
)
from shared.logging.context import (
    set_log_context,
    get_log_context,
    LogContext,
    log_context,
)
from shared.logging.decorators import log_execution

__all__ = [
    "setup_logging",
    "get_logger",
    "LogConfig",
    "set_log_context",
    "get_log_context",
    "LogContext",
    "log_context",
    "log_execution",
]
