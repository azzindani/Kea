
"""
Main Unified Logging Standard.
Provides a standardized logger with consistent symbols, coloring, flag support, and standardized I/O.
Fully compliant with MCP JSON-RPC 2.0 and RFC 5424 severity levels.
"""

import json
import logging
import os
import sys
import uuid
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
from contextlib import contextmanager

import structlog
from pydantic import BaseModel, Field

# ============================================================================
# 🎭 Level & Symbol standards
# ============================================================================

class LogLevel(str, Enum):
    """Standard log levels (RFC 5424 / Syslog compliance)."""
    DEBUG = "debug"
    INFO = "info"
    NOTICE = "notice"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    ALERT = "alert"
    EMERGENCY = "emergency"

class LogConfig:
    """Compatibility container for logging configuration."""
    def __init__(self, level: str | None = None, format: str | None = None, service_name: str = "app"):
        from shared.config import get_settings
        settings = get_settings()
        self.level = (level or settings.logging.level).lower()
        self.format = format or settings.logging.format
        self.service_name = service_name

LEVEL_SYMBOLS = {
    "debug": "🔍", "info": "ℹ️ ", "success": "✅", "notice": "🔔",
    "warning": "⚠️ ", "error": "❌", "critical": "💀", "alert": "🚨", "emergency": "☢️ "
}

def _get_rich_theme():
    try:
        from rich.theme import Theme
        return Theme({
            "logging.level.success": "bold green",
            "logging.level.info": "bold blue",
            "logging.level.notice": "bold cyan italic",
            "logging.level.warning": "bold yellow",
            "logging.level.error": "bold red",
            "logging.level.critical": "bold magenta reverse",
            "logging.level.alert": "bold red reverse",
            "logging.level.emergency": "bold red blink reverse",
            "logging.level.debug": "cyan",
            "log.timestamp": "blue",
            "log.logger": "magenta",
            "log.key": "cyan",
            "log.value": "green",
        })
    except ImportError:
        return None

# Defaults (updated by setup_logging)
DEFAULT_FLAGS = {
    "env": "unknown",
    "version": "unknown",
}

# ============================================================================
# 📊 Metrics (Prometheus)
# ============================================================================

try:
    from prometheus_client import Counter, Histogram, Info
    METRICS_ENABLED = True
    API_REQUESTS = Counter("system_api_requests_total", "Total API requests", ["method", "endpoint", "status_code"])
    API_DURATION = Histogram("system_api_duration_seconds", "API request duration", ["method", "endpoint"])
    LLM_REQUESTS = Counter("system_llm_requests_total", "Total LLM requests", ["provider", "model", "status"])
    LLM_TOKENS = Counter("system_llm_tokens_total", "Total tokens used", ["provider", "model", "token_type"])
    # System Info
    SYSTEM_INFO = Info("system_info", "Static system information")
    
    # Tool Metrics
    TOOL_INVOCATIONS = Counter(
        "system_tool_invocations_total", "Total tool calls", ["tool", "status"]
    )

except ImportError:
    METRICS_ENABLED = False

def set_system_info(version: str, environment: str):
    """Set global system information metrics."""
    if METRICS_ENABLED:
        SYSTEM_INFO.info({"version": version, "environment": environment})

def record_api_request(method: str, endpoint: str, status_code: int, duration: float):
    if METRICS_ENABLED:
        API_REQUESTS.labels(method=method, endpoint=endpoint, status_code=str(status_code)).inc()
        API_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

def record_llm_request(provider: str, model: str, status: str):
    if METRICS_ENABLED:
        LLM_REQUESTS.labels(provider=provider, model=model, status=status).inc()

def record_llm_tokens(provider: str, model: str, prompt_tokens: int, completion_tokens: int):
    if METRICS_ENABLED:
        LLM_TOKENS.labels(provider=provider, model=model, token_type="prompt").inc(prompt_tokens)
        LLM_TOKENS.labels(provider=provider, model=model, token_type="completion").inc(completion_tokens)

# ============================================================================
# 📥 Standardized I/O Models
# ============================================================================

class IOType(str, Enum):
    """Types of I/O operations."""
    INPUT = "input"
    OUTPUT = "output"
    ERROR = "error"
    RPC_REQUEST = "rpc_request"
    RPC_RESPONSE = "rpc_response"
    RPC_NOTIFICATION = "rpc_notification"
    STREAM = "stream"
    STATE_CHANGE = "state_change"
    COGNITIVE_STEP = "cognitive_step"

class IOEnvelope(BaseModel):
    """Standardized I/O Envelope for consistent cross-service telemetry."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: IOType
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    source: str
    target: str | None = None
    trace_id: str | None = None
    request_id: str | None = None
    session_id: str | None = None
    data: Any
    schema_ref: str | None = None
    proto: str = "json"

    class Config:
        use_enum_values = True

class JSONRPCLog(BaseModel):
    """Standardized JSON-RPC 2.0 log entry."""
    jsonrpc: str = "2.0"
    id: Union[str, int, None] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

# ============================================================================
# 🖥️ Rendering & Configuration
# ============================================================================

class ConsoleRenderer:
    """Custom structlog renderer via Rich to console (bypassing stdlib to fix Pytest mangling)."""
    def __init__(self, colors: bool = True):
        self._colors = colors
        self._rich_available = False
        try:
            from rich.console import Console
            # force_terminal=True ensures rich outputs ANSI even if piped, keeping colors!
            self.console = Console(theme=_get_rich_theme(), stderr=True, force_terminal=colors, soft_wrap=True)
            self._rich_available = True
        except ImportError:
            self.console = None

    def __call__(self, logger: Any, method_name: str, event_dict: Dict[str, Any]) -> str:
        level = method_name.lower()
        symbol = LEVEL_SYMBOLS.get(level, "•")
        timestamp = event_dict.pop("timestamp", datetime.now().strftime("%H:%M:%S"))
        logger_name = event_dict.pop("logger", "root")
        message = str(event_dict.pop("event", ""))

        if self._colors and self._rich_available:
            # Escape message for rich markup
            message_safed = message.replace("[", "\\[")
            
            flags = []
            for key, value in event_dict.items():
                if key in ("level", "timestamp", "logger", "exception", "io", "env", "version"):
                    continue
                val_str = str(value).replace("[", "\\[")
                flags.append(f"\\[[bold cyan]{key}[/]=[green]{val_str}[/]]")

            io_hint = ""
            if "io" in event_dict:
                io_type = event_dict["io"].get("type", "unknown").upper()
                io_hint = f" \\[[bold yellow]IO:{io_type}[/]]"

            theme_level = f"logging.level.{level}" 
            if level not in LEVEL_SYMBOLS:
                theme_level = "bold blue"

            # Adding bold cyan, bold magenta, green, blue for maximum diversity
            head = f"\\[[bold blue]{timestamp}[/]] \\[[{theme_level}]{symbol} {level.upper():<8}[/]] \\[[bold magenta]{logger_name:<12}[/]]"
            
            tail = ""
            if flags:
                tail = " [bold yellow]→[/] " + " ".join(flags)

            markup = f"{head}{io_hint} {message_safed}{tail}"
            
            self.console.print(markup)
            
            import structlog
            raise structlog.DropEvent
        else:
            # Fallback pure string for standard logging without rich
            flags = []
            for key, value in event_dict.items():
                if key in ("level", "timestamp", "logger", "exception", "io", "env", "version"):
                    continue
                flags.append(f"[{key}={value}]")
            
            io_hint = ""
            if "io" in event_dict:
                io_type = event_dict["io"].get("type", "unknown").upper()
                io_hint = f" [IO:{io_type}]"
                
            tail = " → " + " ".join(flags) if flags else ""
            return f"[{timestamp}] [{symbol} {level.upper():<8}] [{logger_name:<12}]{io_hint} {message}{tail}"

def setup_logging(config: Optional[Union[LogConfig, str]] = None, level: Optional[str] = None, force_stderr: bool = True):
    """Standardized logging setup for all codebases."""
    from shared.config import get_settings
    settings = get_settings()
    
    # Update global flags
    DEFAULT_FLAGS["env"] = settings.app.environment
    DEFAULT_FLAGS["version"] = settings.app.version
    
    raw_level = (config.level if isinstance(config, LogConfig) else (config if isinstance(config, str) else settings.logging.level)).lower()
    log_format = settings.logging.format.lower()

    root_logger = logging.getLogger()

    # ── Purge ALL existing handlers (ours, pytest's, log-cli, etc.) ──
    root_logger.handlers = []
    for name in logging.root.manager.loggerDict:
        lg = logging.getLogger(name)
        lg.handlers = []
        lg.propagate = True

    # ── Build our single, authoritative handler ──
    stream = sys.stderr if force_stderr else sys.stdout
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(message)s"))

    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, raw_level.upper()))
    
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="%H:%M:%S", utc=False),
    ]
    processors.append(ConsoleRenderer() if log_format == "console" else structlog.processors.JSONRenderer())
        
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    for lib in ("httpx", "httpcore", "asyncio", "urllib3"):
        logging.getLogger(lib).setLevel(logging.WARNING)

# ============================================================================
# 🛡️ Suppression & Middleware
# ============================================================================

@contextmanager
def suppress_stdout():
    """Silence stdout to prevent noise."""
    with open(os.devnull, "w", encoding="utf-8") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try: yield
        finally: sys.stdout = old_stdout

try:
    from starlette.middleware.base import BaseHTTPMiddleware
    
    class RequestLoggingMiddleware(BaseHTTPMiddleware):
        """Standardized FastAPI middleware for logging and metrics."""
        async def dispatch(self, request: Any, call_next: Callable) -> Any:
            rid = request.headers.get("X-Request-ID", f"req-{uuid.uuid4().hex[:8]}")
            tid = request.headers.get("X-Trace-ID", uuid.uuid4().hex)
            bind_contextvars(request_id=rid, trace_id=tid, method=request.method, path=request.url.path)
            
            get_logger("http").info(f"▶️  {request.method} {request.url.path}")
            start = time.perf_counter()
            try:
                response = await call_next(request)
                duration = time.perf_counter() - start
                get_logger("http").info(f"✅ {response.status_code}", duration_ms=round(duration*1000, 2))
                record_api_request(request.method, request.url.path, response.status_code, duration)
                response.headers["X-Request-ID"] = rid
                return response
            except Exception as e:
                duration = time.perf_counter() - start
                get_logger("http").error("❌ Request failed", error=str(e), exc_info=True)
                record_api_request(request.method, request.url.path, 500, duration)
                raise
            finally: clear_contextvars()
except ImportError:
    pass

# ============================================================================
# 💉 Factory & Helpers
# ============================================================================

def bind_contextvars(**kwargs): structlog.contextvars.bind_contextvars(**kwargs)
def clear_contextvars(): structlog.contextvars.clear_contextvars()
def get_logger(name: str) -> structlog.stdlib.BoundLogger: 
    # Lazy sync of default flags if they are still unknown
    if DEFAULT_FLAGS["env"] == "unknown":
        try:
            from shared.config import get_settings
            settings = get_settings()
            DEFAULT_FLAGS["env"] = settings.app.environment
            DEFAULT_FLAGS["version"] = settings.app.version
        except Exception:
            pass
    return structlog.get_logger(name).bind(**DEFAULT_FLAGS)

def log_input(source: str, data: Any, **kw):
    env = IOEnvelope(type=IOType.INPUT, source=source, data=data, **kw)
    get_logger("io").info(f"📥 INPUT from {source}", io=env.model_dump())

def log_output(source: str, data: Any, **kw):
    env = IOEnvelope(type=IOType.OUTPUT, source=source, data=data, **kw)
    get_logger("io").info(f"📤 OUTPUT from {source}", io=env.model_dump())

def log_error(source: str, err: Any, **kw):
    env = IOEnvelope(type=IOType.ERROR, source=source, data=str(err), **kw)
    get_logger("io").error(f"❌ ERROR in {source}", io=env.model_dump())

def log_rpc_call(source: str, target: str, method: str, params: Any, rpc_id: Optional[Union[str, int]] = None, **kw):
    rpc = JSONRPCLog(id=rpc_id, method=method, params=params)
    env = IOEnvelope(type=IOType.RPC_REQUEST, source=source, target=target, data=rpc.model_dump(exclude_none=True), proto="json-rpc", **kw)
    get_logger("io").info(f"📡 RPC CALL {source} -> {target}: {method}", io=env.model_dump())

def log_rpc_response(source: str, target: str, rpc_id: Union[str, int], result: Any = None, error: Any = None, **kw):
    rpc = JSONRPCLog(id=rpc_id, result=result, error=error)
    env = IOEnvelope(type=IOType.RPC_RESPONSE, source=source, target=target, data=rpc.model_dump(exclude_none=True), proto="json-rpc", **kw)
    get_logger("io").info(f"🏁 RPC RESP {source} -> {target}", io=env.model_dump())

def log_mcp_message(source: str, level: LogLevel, data: Any, logger_name: Optional[str] = None, **kw):
    """Log an MCP standardized notification (notifications/message)."""
    rpc = JSONRPCLog(method="notifications/message", params={"level": level.value, "logger": logger_name, "data": data})
    env = IOEnvelope(type=IOType.RPC_NOTIFICATION, source=source, data=rpc.model_dump(exclude_none=True), proto="json-rpc", **kw)
    get_logger("io").info(f"📢 MCP LOG [{level.value}] from {source}", io=env.model_dump())

def success(self, event, **kw): return self._proxy_to_logger("info", event, **{**kw, "level": "success"})
structlog.stdlib.BoundLogger.success = success


# ============================================================================
# 🤖 LLM Interaction Helpers (Premium Test Mode Visibility)
# ============================================================================

def _get_rich_console():
    """Get a shared rich console for test rendering."""
    try:
        from rich.console import Console
        return Console(theme=_get_rich_theme(), stderr=True)
    except ImportError:
        return None

def log_llm_request(logger: Any, messages: List[Union[Dict[str, Any], Any]], model: str):
    """
    Log an LLM request. In TEST_MODE, uses premium multi-line formatting via direct console print.
    Otherwise, uses standard structured logging.
    """
    # Always log the structured data for telemetry
    logger.debug("LLM Request", messages=[
        {"role": m.role.value if hasattr(m.role, "value") else str(m.role), "content": m.content} 
        if hasattr(m, "role") else m for m in messages
    ], model=model)

    if os.getenv("TEST_MODE") == "1":
        console = _get_rich_console()
        if not console: return

        # Premium Test Mode View
        timestamp = datetime.now().strftime("%H:%M:%S")
        lines = [f"\n\\[[bold blue]{timestamp}[/]] [bold cyan]LLM Request[/] [magenta]({model})[/]"]
        lines.append("[bold cyan]" + "━" * 88 + "[/]")
        for m in messages:
            role = "unknown"
            content = ""
            if hasattr(m, "role") and hasattr(m, "content"):
                role = m.role.value if hasattr(m.role, "value") else str(m.role)
                content = m.content
            elif isinstance(m, dict):
                role = str(m.get("role", "unknown"))
                content = str(m.get("content", ""))
            
            role_style = "bold magenta" if role == "system" else "bold green" if role == "user" else "bold cyan"
            # Escape content to prevent rich markup issues
            escaped_content = str(content).replace("[", "\\[")
            lines.append(f"[{role_style}]{role.upper():<9}[/] {escaped_content}")
        lines.append("[bold cyan]" + "━" * 88 + "[/]")
        console.print("\n".join(lines))

def log_llm_response(logger: Any, content: str, model: str, reasoning: Optional[str] = None, event_name: str = "LLM Response"):
    """
    Log an LLM response. In TEST_MODE, uses premium multi-line formatting via direct console print.
    Otherwise, uses standard structured logging.
    """
    # Always log the structured data for telemetry
    logger.debug(event_name, content=content, reasoning=reasoning, model=model)

    if os.getenv("TEST_MODE") == "1":
        console = _get_rich_console()
        if not console: return

        # Premium Test Mode View
        timestamp = datetime.now().strftime("%H:%M:%S")
        lines = [f"\n\\[[bold blue]{timestamp}[/]] [bold green]{event_name}[/] [magenta]({model})[/]"]
        lines.append("[bold cyan]" + "━" * 88 + "[/]")
        
        # Attempt to pretty-print JSON if possible
        display_content = str(content)
        try:
            if display_content.strip().startswith(("{", "[")):
                parsed = json.loads(display_content)
                display_content = json.dumps(parsed, indent=2)
        except Exception:
            pass

        # Escape content to prevent rich markup issues
        escaped_content = display_content.replace("[", "\\[")
        lines.append(escaped_content)
        if reasoning:
            lines.append(f"\n[bold yellow]Reasoning:[/] [cyan]{str(reasoning).replace('[', '\\[')}[/]")
        lines.append("[bold cyan]" + "━" * 88 + "[/]")
        console.print("\n".join(lines))
