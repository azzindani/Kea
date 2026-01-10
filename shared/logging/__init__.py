"""
Structured Logging Package.

Provides:
- Structured JSON logging
- OpenTelemetry trace correlation
- FastAPI middleware
- Logging decorators
"""

from shared.logging.structured import (
    get_logger,
    setup_logging,
    LogConfig,
)
from shared.logging.context import (
    LogContext,
    get_context,
    set_context,
)

__all__ = [
    "get_logger",
    "setup_logging",
    "LogConfig",
    "LogContext",
    "get_context",
    "set_context",
]
