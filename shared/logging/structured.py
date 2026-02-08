"""
Structured Logging Implementation.

Provides JSON logging with configurable output and trace correlation.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel


class LogLevel(str, Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogConfig(BaseModel):
    """Logging configuration."""
    level: LogLevel = LogLevel.INFO
    format: str = "console"  # json or console
    service_name: str = "research-engine"
    include_timestamp: bool = True
    include_trace: bool = True


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.
    
    Produces logs in the format:
    {
        "timestamp": "2026-01-10T19:00:00.000Z",
        "level": "INFO",
        "service": "orchestrator",
        "trace_id": "abc123",
        "span_id": "def456",
        "request_id": "req-789",
        "message": "Processing request",
        "context": {...}
    }
    """
    
    def __init__(self, service_name: str = "research-engine") -> None:
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        try:
            from shared.logging.context import get_context
            ctx = get_context()
        except ImportError:
            # During shutdown, imports might fail
            class MockContext:
                trace_id = None
                span_id = None
                request_id = None
            ctx = MockContext()
        
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "logger": record.name,
            # "message": record.getMessage(),
        }
        
        try:
            log_entry["message"] = record.getMessage()
        except Exception:
             log_entry["message"] = str(record.msg) + (f" {record.args}" if record.args else "")
        
        # Add trace context if available
        if ctx.trace_id:
            log_entry["trace_id"] = ctx.trace_id
        if ctx.span_id:
            log_entry["span_id"] = ctx.span_id
        if ctx.request_id:
            log_entry["request_id"] = ctx.request_id
        
        # Add extra context
        extra_context = {}
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "exc_text", "thread", "threadName",
                "message", "taskName"
            ):
                extra_context[key] = value
        
        if extra_context:
            log_entry["context"] = extra_context
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


class ConsoleFormatter(logging.Formatter):
    """
    Colored console formatter for development.
    """
    
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        try:
            from shared.logging.context import get_context
            ctx = get_context()
        except ImportError:
            # During shutdown, imports might fail
            class MockContext:
                trace_id = None
                request_id = None
            ctx = MockContext()
            
        color = self.COLORS.get(record.levelname, "")
        
        # Build prefix
        prefix_parts = []
        if ctx.request_id:
            prefix_parts.append(f"[{ctx.request_id[:8]}]")

        # Handle trace_id differently based on formatter
        if hasattr(ctx, 'trace_id') and ctx.trace_id:
             prefix_parts.append(f"<{ctx.trace_id[:8]}>")
        
        prefix = " ".join(prefix_parts)
        if prefix:
            prefix = f"{prefix} "
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        try:
            message = record.getMessage()
        except Exception:
            message = str(record.msg) + (f" {record.args}" if record.args else "")

        return (
            f"{color}[{timestamp}] {record.levelname:8}{self.RESET} "
            f"{prefix}{record.name}: {message}"
        )


def setup_logging(config: LogConfig | None = None) -> None:
    """
    Setup logging with the given configuration.
    
    Args:
        config: Logging configuration (uses defaults if not provided)
    """
    if config is None:
        config = LogConfig()
    
    # Remove existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Create handler
    # Create handler
    handler = logging.StreamHandler(sys.stderr)
    
    # Set formatter based on format type
    if config.format == "json":
        handler.setFormatter(JSONFormatter(service_name=config.service_name))
    else:
        handler.setFormatter(ConsoleFormatter())
    
    # Configure root logger
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, config.level.value))
    
    # Set levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("datasets").setLevel(logging.WARNING)
    logging.getLogger("tensorflow").setLevel(logging.WARNING)
    logging.getLogger("jax").setLevel(logging.WARNING)
    logging.getLogger("pydot").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("filelock").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)
    
    # Configure structlog to output to stderr
    try:
        import structlog
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer(colors=config.format == "console")
                if config.format == "console"
                else structlog.processors.JSONRenderer(),
            ],
            logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
            cache_logger_on_first_use=True,
        )
    except ImportError:
        pass


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger
    """
    return logging.getLogger(name)
