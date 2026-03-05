
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
from structlog import DropEvent
from pydantic import BaseModel, Field

# ============================================================================
# ── UNIVERSAL TELEMETRY FACTORY ──
# ============================================================================
# Standardized bridge for extended RFC 5424 severity levels.
def _get_telemetry_method(name: str):
    """Creates a standardized logging proxy for success, notice, alert, emergency."""
    level_map = {"success": "info", "notice": "info", "alert": "error", "emergency": "critical"}
    def _method(self, event: str, **kw: Any) -> Any:
        # 1. Try proxy-to-logger (Standard for stdlib filtered loggers)
        proxy = getattr(self, "_proxy_to_logger", None)
        if proxy:
            return proxy(level_map[name], event, **{**kw, "level": name})
        # 2. Try direct call on the underlying standard method
        target = getattr(self, level_map[name], getattr(self, "info", None))
        if target:
            return target(event, **{**kw, "level": name})
        return None
    return _method

def _apply_universal_telemetry_patch():
    """Recursively patches all structlog logger base classes and dynamic proxies."""
    try:
        import structlog.stdlib
        
        # 1. Base Targets: Start with the most foundational bases
        # We target structlog._base.BoundLoggerBase as it's the root of all dynamic filtered loggers
        bases = [structlog.BoundLogger, structlog.PrintLogger]
        
        # Access internal base directly for deepest possible patching
        try:
            import structlog._base
            if hasattr(structlog._base, "BoundLoggerBase"):
                bases.append(structlog._base.BoundLoggerBase)
        except (ImportError, AttributeError):
            pass

        if hasattr(structlog, "stdlib") and hasattr(structlog.stdlib, "BoundLogger"):
            bases.append(structlog.stdlib.BoundLogger)

        # 2. Recursive Patching of all existing subclasses (including live dynamic proxies)
        def _patch_recursive(cls):
            # Apply to this class
            for m in ["success", "notice", "alert", "emergency"]:
                if not hasattr(cls, m):
                    try:
                        setattr(cls, m, _get_telemetry_method(m))
                    except Exception: pass
            
            # Recurse into all discovered subclasses
            try:
                for sub in cls.__subclasses__():
                    _patch_recursive(sub)
            except Exception: pass

        for base in bases:
            _patch_recursive(base)

        # 3. Factory Hook: Catch any FUTURE dynamically created filtering loggers
        if hasattr(structlog.stdlib, "make_filtering_bound_logger"):
            orig_factory = structlog.stdlib.make_filtering_bound_logger
            def patched_factory(*args, **kwargs):
                cls = orig_factory(*args, **kwargs)
                for m in ["success", "notice", "alert", "emergency"]:
                    if not hasattr(cls, m):
                        setattr(cls, m, _get_telemetry_method(m))
                return cls
            structlog.stdlib.make_filtering_bound_logger = patched_factory
    except Exception:
        pass

# Immediate application for top-level loggers
_apply_universal_telemetry_patch()

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
    "debug": "🔍", "info": "ℹ️", "success": "✅", "notice": "🔔",
    "warning": "⚠️", "error": "❌", "critical": "💀", "alert": "🚨", "emergency": "☢️"
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
# ⚙️ Internal Helpers
# ============================================================================

def _truncate_data(data: Any, max_len: int = 2000, max_depth: int = 3, current_depth: int = 0) -> Any:
    """Recursively truncate nested data structures to prevent log bloat and OOM."""
    if current_depth > max_depth:
        return "[Depth Limit Exceeded]"
    
    if isinstance(data, str):
        if len(data) > max_len:
            return data[:max_len] + f"\n[... truncated {len(data) - max_len} chars]"
        return data
    
    if isinstance(data, list):
        if not data: return []
        # Support for list truncation
        limit = 20 # Max items in a list for logging
        truncated = [_truncate_data(item, max_len, max_depth, current_depth + 1) for item in data[:limit]]
        if len(data) > limit:
            truncated.append(f"[... truncated {len(data) - limit} items]")
        return truncated
    
    if isinstance(data, dict):
        if not data: return {}
        # Support for dict truncation
        res = {}
        for i, (k, v) in enumerate(data.items()):
            if i >= 30: # Max keys in a dict for logging
                res["[... truncated keys]"] = f"{len(data) - 30} more"
                break
            res[k] = _truncate_data(v, max_len, max_depth, current_depth + 1)
        return res
    
    if isinstance(data, (int, float, bool, type(None))):
        return data
        
    if hasattr(data, "model_dump") and callable(getattr(data, "model_dump")):
        try:
            # Prevent infinite recursion if model_dump() returns the same object
            dumped = data.model_dump()
            if not isinstance(dumped, type(data)):
                return _truncate_data(dumped, max_len, max_depth, current_depth + 1)
        except Exception:
            pass
            
    if hasattr(data, "dict") and callable(getattr(data, "dict")):
        try:
            dumped = data.dict()
            if not isinstance(dumped, type(data)):
                return _truncate_data(dumped, max_len, max_depth, current_depth + 1)
        except Exception:
            pass
            
    # Fallback to string representation for safe JSON serialization downstream
    return _truncate_data(repr(data), max_len, max_depth, current_depth + 1)

# ============================================================================
# 🖥️ Rendering & Configuration
# ============================================================================

import re

def _colorize_message(msg: str) -> str:
    """Make arbitrary raw text heavily colored and formatted for Rich console."""
    m = str(msg).replace("[", "\\[")
    
    # Transform `Word=value` or `Word: value` into colored brackets
    def kv_replacer(match):
        k = match.group(1)
        v = match.group(2)
        # Prevent mis-coloring URLs as keys (e.g. http: //...)
        if k.lower() in ("http", "https", "file"):
            return match.group(0)
        
        # Colorize true/false specifically within values
        if v.lower() == "true":
            v = f"[bold green]{v}[/]"
        elif v.lower() == "false":
            v = f"[bold red]{v}[/]"
        elif v.isdigit() or v.replace('.', '', 1).isdigit():
            v = f"[bold magenta]{v}[/]"
            
        return f"\\[[bold cyan]{k}[/]=[green]{v}[/]]"

    
    # regex for key-value pairs (e.g. key=value or key: value)
    # Optimized to avoid backtracking on large strings
    m = re.sub(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*[=]\s*([^\s\\[\\]\'\"]{1,500})', kv_replacer, m)
    m = re.sub(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*[:]\s*([^\s\\[\\]\'\"]{1,500})', kv_replacer, m)
    
    # Colorize any single or double quoted strings (limit length to prevent regex explosion)
    m = re.sub(r"('[^']{1,500}')", r"[yellow]\1[/]", m)
    m = re.sub(r'("[^"]{1,500}")', r"[yellow]\1[/]", m)
    
    return m

class ConsoleRenderer:
    """Custom structlog renderer via Rich to console (bypassing stdlib to fix Pytest mangling)."""
    def __init__(self, colors: bool = True):
        self._colors = colors
        self._rich_available = False
        try:
            from rich.console import Console
            # force_terminal=True ensures rich outputs ANSI even if piped, keeping colors!
            # width=140 gives it a wide preview format but prevents infinite sliders by forcing a wrap at 140 columns
            self.console = Console(theme=_get_rich_theme(), stderr=True, force_terminal=colors, width=140)
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
            # Use incredibly diverse text coloring on the raw payload
            # Limit message length for colorization to prevent regex performance issues
            message_colored = _colorize_message(message[:5000])
            
            io_hint = ""
            if "io" in event_dict:
                try:
                    io_val = event_dict["io"]
                    if isinstance(io_val, dict):
                        io_type = io_val.get("type", "unknown").upper()
                        io_hint = f" \\[[bold yellow]IO:{io_type}[/]]"
                        
                        # Flatten IO data into the dict so it renders as flags
                        io_data = io_val.get("data")
                        if isinstance(io_data, dict):
                            for k, v in io_data.items():
                                if k not in event_dict:
                                    event_dict[k] = v
                        elif io_data is not None:
                            event_dict["data"] = io_data
                except Exception:
                    pass

            flags = []
            for key, value in event_dict.items():
                if key in ("level", "timestamp", "logger", "exception", "io", "env", "version"):
                    continue
                
                # Defensively truncate large objects to prevent console overflow or memory crashes
                safe_val = _truncate_data(value, max_len=1000, max_depth=2)
                val_str = str(safe_val).replace("[", "\\[")
                
                if val_str.lower() == "true":
                    val_str = f"[bold green]{val_str}[/]"
                elif val_str.lower() == "false":
                    val_str = f"[bold red]{val_str}[/]"
                elif val_str.isdigit() or val_str.replace('.', '', 1).isdigit():
                    val_str = f"[bold magenta]{val_str}[/]"
                
                flags.append(f"\\[[bold cyan]{key}[/]=[green]{val_str}[/]]")

            theme_level = f"logging.level.{level}" 
            if level not in LEVEL_SYMBOLS:
                theme_level = "bold blue"

            # Strict Brackets: [Time] [Level] [Logger] Symbol
            # (Symbol placed at the end of the block so varying emoji widths never misalign the columns)
            head = f"\\[[bold blue]{timestamp}[/]] \\[[{theme_level}]{level.upper():<8}[/]] \\[[bold magenta]{logger_name:<12}[/]] {symbol}"
            
            tail = ""
            if flags:
                tail = " [bold yellow]→[/] " + " ".join(flags)

            markup = f"{head}{io_hint} {message_colored}{tail}"
            
            self.console.print(markup)
            raise DropEvent
        else:
            # Fallback pure string for standard logging without rich
            io_hint = ""
            if "io" in event_dict:
                try:
                    io_val = event_dict["io"]
                    if isinstance(io_val, dict):
                        io_type = io_val.get("type", "unknown").upper()
                        io_hint = f" [IO:{io_type}]"
                        
                        # Flatten IO data
                        io_data = io_val.get("data")
                        if isinstance(io_data, dict):
                            for k, v in io_data.items():
                                if k not in event_dict:
                                    event_dict[k] = v
                        elif io_data is not None:
                            event_dict["data"] = io_data
                except Exception:
                    pass

            flags = []
            for key, value in event_dict.items():
                if key in ("level", "timestamp", "logger", "exception", "io", "env", "version"):
                    continue
                safe_val = _truncate_data(value, max_len=1000, max_depth=2)
                flags.append(f"[{key}={safe_val}]")
                
            tail = " → " + " ".join(flags) if flags else ""
            return f"[{timestamp}] [{symbol} {level.upper():<8}] [{logger_name:<12}]{io_hint} {message}{tail}"

class UnifiedBoundLogger(structlog.stdlib.BoundLogger):
    """Custom BoundLogger to support extended RFC 5424 log levels."""
    
    def success(self, event: str, **kw: Any) -> Any:
        return self._proxy_to_logger("info", event, **{**kw, "level": "success"})

    def notice(self, event: str, **kw: Any) -> Any:
        return self._proxy_to_logger("info", event, **{**kw, "level": "notice"})

    def alert(self, event: str, **kw: Any) -> Any:
        return self._proxy_to_logger("error", event, **{**kw, "level": "alert"})

    def emergency(self, event: str, **kw: Any) -> Any:
        return self._proxy_to_logger("critical", event, **{**kw, "level": "emergency"})

import threading
_LOGGING_LOCK = threading.Lock()
_LOGGING_CONFIGURED = False

def setup_logging(config: Optional[Union[LogConfig, str]] = None, level: Optional[str] = None, force_stderr: bool = True):
    """Standardized logging setup for all codebases."""
    global _LOGGING_CONFIGURED
    
    if _LOGGING_CONFIGURED:
        return

    with _LOGGING_LOCK:
        if _LOGGING_CONFIGURED:
            return
        _LOGGING_CONFIGURED = True

    from shared.config import get_settings
    settings = get_settings()
    
    # Update global flags
    DEFAULT_FLAGS["env"] = settings.app.environment
    DEFAULT_FLAGS["version"] = settings.app.version
    
    raw_level = (config.level if isinstance(config, LogConfig) else (config if isinstance(config, str) else settings.logging.level)).lower()
    log_format = settings.logging.format.lower()

    root_logger = logging.getLogger()

    # ── Preserve pytest's log-capture handlers so test output remains visible ──
    # pytest installs LogCaptureHandler (live-log) and _LiveLoggingStreamHandler
    # on the root logger before pytest_configure runs.  Purging them blindly
    # silences all service-check and crash messages from pytest's "LIVE LOG"
    # sections — making the actual failure location invisible to the user.
    pytest_handlers = [
        h for h in root_logger.handlers
        if getattr(type(h), "__module__", "").startswith("_pytest")
        or type(h).__name__ in ("LogCaptureHandler", "LiveLoggingStreamHandler")
    ]

    # ── Purge non-pytest handlers from root and all child loggers ──
    root_logger.handlers = [h for h in root_logger.handlers if h in pytest_handlers]
    # Use list() to avoid "dictionary changed size during iteration" crash
    for name in list(logging.root.manager.loggerDict.keys()):
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
        structlog.stdlib.filter_by_level,
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
        wrapper_class=UnifiedBoundLogger,
        cache_logger_on_first_use=True,
    )

_apply_universal_telemetry_patch()

# Suppress noisy framework / infrastructure loggers
for lib in (
    "httpx", "httpcore", "asyncio", "urllib3",
    # Jupyter / IPython kernel internals
        "IPKernelApp", "ipykernel", "jupyter_client", "jupyter_core",
        "traitlets", "tornado", "zmq",
        # ML framework noise
        "matplotlib", "PIL", "jax", "absl",
        "tensorflow", "torch", "torchao",
        # Misc
        "pydot", "numexpr", "parso",
    ):
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
    """Get a standardized logger with unified metadata and safety hooks."""
    # Lazy environment sync
    if DEFAULT_FLAGS["env"] == "unknown":
        try:
            import sys
            if "shared.config" in sys.modules:
                from shared.config import get_settings
                settings = get_settings()
                DEFAULT_FLAGS["env"] = str(settings.app.environment.value if hasattr(settings.app.environment, "value") else settings.app.environment)
                DEFAULT_FLAGS["version"] = settings.app.version
        except Exception:
            pass
            
    logger = structlog.get_logger(name)
    
    # --- RIGOROUS ON-THE-FLY PATCHING ---
    # Final safety layer: If structlog generated a class we missed during startup scan
    # (common in dynamic environments like Pytest), we patch both the instance class 
    # and the result of .bind() to ensure total coverage.
    def _ensure_telemetry(obj):
        if not obj: return
        cls = obj.__class__
        for m in ["success", "notice", "alert", "emergency"]:
            if not hasattr(cls, m):
                 try:
                     setattr(cls, m, _get_telemetry_method(m))
                 except Exception: pass

    _ensure_telemetry(logger)
    bound_logger = logger.bind(**DEFAULT_FLAGS)
    _ensure_telemetry(bound_logger)

    return bound_logger

def log_input(source: str, data: Any, **kw):
    env = IOEnvelope(type=IOType.INPUT, source=source, data=data, **kw)
    get_logger("io").debug(f"📥 INPUT from {source}", io=env.model_dump())

def log_output(source: str, data: Any, **kw):
    env = IOEnvelope(type=IOType.OUTPUT, source=source, data=data, **kw)
    get_logger("io").debug(f"📤 OUTPUT from {source}", io=env.model_dump())

def log_error(source: str, err: Any, **kw):
    error_data = err if isinstance(err, (dict, list)) else str(err)
    env = IOEnvelope(type=IOType.ERROR, source=source, data=error_data, **kw)
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

# ============================================================================
# 🤖 LLM Interaction Helpers (Premium Test Mode Visibility)
# ============================================================================

# Global singleton console to prevent resource leaks and initialization overhead
_GLOBAL_RICH_CONSOLE: Optional[Any] = None

def _get_rich_console():
    """Get a shared rich console singleton for optimized rendering."""
    global _GLOBAL_RICH_CONSOLE
    if _GLOBAL_RICH_CONSOLE is not None:
        return _GLOBAL_RICH_CONSOLE
        
    try:
        from rich.console import Console
        # width=None allows the console to detect terminal width automatically
        _GLOBAL_RICH_CONSOLE = Console(theme=_get_rich_theme(), stderr=True, width=140)
        return _GLOBAL_RICH_CONSOLE
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
            
            # STABILIZATION: Truncate large prompt content
            truncated_content = _truncate_data(content, max_len=1500)
            
            role_style = "bold magenta" if role == "system" else "bold green" if role == "user" else "bold cyan"
            # Escape content to prevent rich markup issues
            escaped_content = str(truncated_content).replace("[", "\\[")
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

        # STABILIZATION: Truncate large response content
        truncated_content = _truncate_data(content, max_len=2000)
        truncated_reasoning = _truncate_data(reasoning, max_len=1000) if reasoning else None

        # Escape content to prevent rich markup issues
        escaped_content = str(truncated_content).replace("[", "\\[")
        lines.append(escaped_content)
        if truncated_reasoning:
            lines.append(f"\n[bold yellow]Reasoning:[/] [cyan]{str(truncated_reasoning).replace('[', '\\[')}[/]")
        lines.append("[bold cyan]" + "━" * 88 + "[/]")
        console.print("\n".join(lines))

def log_node_assembly(logger: Any, node_id: str, type: str, layers: List[str], input_schema: Any = None, output_schema: Any = None):
    """Log the assembly of a kernel node with visibility into its layers and schemas."""
    logger.info("Node assembly complete", node_id=node_id, type=type, layers_count=len(layers))
    
    if os.getenv("TEST_MODE") == "1" or os.getenv("VERBOSE_LOGGING") == "1":
        console = _get_rich_console()
        if not console: return

        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            lines = [f"\n\\[[bold blue]{timestamp}[/]] 🏗️  [bold yellow]NODE ASSEMBLED: {node_id}[/]"]
            lines.append(f"  • [bold magenta]Action Type:[/] [bold cyan]{type.upper()}[/]")
            lines.append(f"  • [bold magenta]Logic Layers:[/] [green]{' → '.join(layers)}[/]")
            
            if input_schema:
                truncated_in = _truncate_data(str(input_schema), max_len=300)
                lines.append(f"  • [bold magenta]Input Schema:[/] [yellow]{truncated_in}[/]")
            if output_schema:
                truncated_out = _truncate_data(str(output_schema), max_len=300)
                lines.append(f"  • [bold magenta]Output Schema:[/] [yellow]{truncated_out}[/]")
                
            lines.append("[bold cyan]" + "┄" * 88 + "[/]")
            console.print("\n".join(lines))
        except Exception as e:
            logger.warning(f"Failed to render node assembly log: {e}")

def log_dag_blueprint(logger: Any, dag_id: str, objective: str, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]):
    """Log a structured, architect-level blueprint of the DAG."""
    logger.info("DAG Blueprint generated", dag_id=dag_id, node_count=len(nodes), edge_count=len(edges))
    
    if os.getenv("TEST_MODE") == "1" or os.getenv("VERBOSE_LOGGING") == "1":
        console = _get_rich_console()
        if not console: return

        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            lines = [f"\n\\[[bold blue]{timestamp}[/]] 🏗️  [bold yellow]DAG BLUEPRINT: {dag_id}[/]"]
            lines.append(f"[bold cyan]Objective:[/] [green]{objective}[/]")
            lines.append("[bold cyan]" + "━" * 88 + "[/]")
            
            lines.append("[bold magenta]NODES:[/]")
            for n in nodes[:50]: # Limit node count in blueprint to prevent hang
                nid = n.get("id", "??")
                ntype = n.get("type", "??").upper()
                desc = n.get("description", "??")
                truncated_desc = desc[:100] + "..." if len(desc) > 100 else desc
                tool = n.get("tool", "")
                tool_str = f" [bold blue](Tool: {tool})[/]" if tool else ""
                lines.append(f"  • [bold cyan][{nid}][/] [{ntype}]{tool_str} {truncated_desc}...")
                
                inputs = n.get("inputs", [])
                outputs = n.get("outputs", [])
                if inputs or outputs:
                    lines.append(f"    [dim]↳ Inputs: {inputs} | Outputs: {outputs}[/]")

            if len(nodes) > 50:
                lines.append(f"  ... and {len(nodes) - 50} more nodes.")

            if edges:
                lines.append("\n[bold magenta]EDGES (Data Flow):[/]")
                for e in edges[:100]: # Limit edge count
                    u = e.get("from", "??")
                    v = e.get("to", "??")
                    key = e.get("key", "??")
                    lines.append(f"  • [bold cyan]{u}[/] [yellow]──({key})──>[/] [bold cyan]{v}[/]")
                if len(edges) > 100:
                    lines.append(f"  ... and {len(edges) - 100} more edges.")
            else:
                lines.append("\n[bold magenta]EDGES:[/] [dim]None (Parallel execution batching)[/]")

            lines.append("[bold cyan]" + "━" * 88 + "[/]")
            console.print("\n".join(lines))
        except Exception as e:
            logger.warning(f"Failed to render DAG blueprint: {e}")

def log_node_execution_start(logger: Any, node_id: str, description: str, inputs: List[str], input_data: Dict[str, Any]):
    """Log the start of a node execution with n8n-style visibility."""
    logger.info("Node execution starting", node_id=node_id, inputs=inputs)
    
    if os.getenv("TEST_MODE") == "1" or os.getenv("VERBOSE_LOGGING") == "1":
        console = _get_rich_console()
        if not console: return

        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            lines = [f"\n\\[[bold blue]{timestamp}[/]] 🚀 [bold yellow]EXECUTING NODE:[/] [bold cyan]{node_id}[/]"]
            lines.append(f"  • [bold magenta]Task:[/] {description}")
            
            # STABILIZATION: Robust TRUNCATION of input data
            if input_data:
                clean_input = _truncate_data(input_data, max_len=200, max_depth=2)
                lines.append(f"  • [bold magenta]Inputs Resolved:[/] [yellow]{json.dumps(clean_input, indent=2).replace('[', '\\[')}[/]")
            else:
                lines.append("  • [bold magenta]Inputs Resolved:[/] [dim]None (Initial state or fallback)[/]")
            
            lines.append("[bold blue]" + "┄" * 40 + "[/]")
            console.print("\n".join(lines))
        except Exception as e:
            logger.warning(f"Failed to render node start log: {e}")

def log_tool_execution(logger: Any, node_id: str, tool_name: str, arguments: Dict[str, Any], outputs: Dict[str, Any], success: bool, duration_ms: float):
    """Log premium tool execution details for test visibility."""
    logger.info("Tool execution metrics", node_id=node_id, tool=tool_name, success=success, duration_ms=duration_ms)
    
    if os.getenv("TEST_MODE") == "1" or os.getenv("VERBOSE_LOGGING") == "1":
        console = _get_rich_console()
        if not console: return

        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            status_sym = "[bold green]✅ SUCCESS[/]" if success else "[bold red]❌ FAILED[/]"
            lines = [f"\n\\[[bold blue]{timestamp}[/]] ✨ [bold cyan]NODE COMPLETED: {node_id}[/] (via {tool_name})"]
            lines.append(f"  • [bold magenta]Status:[/] {status_sym} [dim]({round(duration_ms, 2)}ms)[/]")
            
            # STABILIZATION: Truncate arguments
            if arguments:
                clean_args = _truncate_data(arguments, max_len=500, max_depth=2)
                arg_json = json.dumps(clean_args, indent=2)
                lines.append(f"  • [bold magenta]Arguments:[/] [yellow]{arg_json.replace('[', '\\[')}[/]")
            
            # STABILIZATION: Robust truncation of outputs
            if outputs:
                main_content = outputs.get("answer") or outputs.get("content") or outputs.get("result")
                if main_content and isinstance(main_content, str):
                    truncated_content = _truncate_data(main_content, max_len=3000)
                    content_escaped = truncated_content.replace("[", "\\[")
                    lines.append(f"  • [bold magenta]Output Content:[/]\n[green]{content_escaped}[/]")
                else:
                    clean_outputs = _truncate_data(outputs, max_len=1000, max_depth=2)
                    out_json = json.dumps(clean_outputs, indent=2)
                    lines.append(f"  • [bold magenta]Outputs Raw (JSON):[/] [green]{out_json.replace('[', '\\[')}[/]")
            
            lines.append("[bold cyan]" + "━" * 88 + "[/]")
            console.print("\n".join(lines))
        except Exception as e:
            logger.warning(f"Failed to render node completion log: {e}")

def log_final_result(logger: Any, objective: str, content: str, artifacts_count: int, trace_id: str):
    """Log a premium, high-fidelity final mission output."""
    logger.info("Mission final results ready", objective=objective, artifacts=artifacts_count)
    
    if os.getenv("TEST_MODE") == "1" or os.getenv("VERBOSE_LOGGING") == "1":
        console = _get_rich_console()
        if not console: return

        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            lines = [f"\n\\[[bold blue]{timestamp}[/]] 🏆 [bold green]MISSION COMPLETE[/]"]
            lines.append(f"[bold cyan]Objective:[/] [green]{objective}[/]")
            lines.append(f"[bold cyan]Trace ID:[/] [magenta]{trace_id}[/]")
            lines.append("[bold cyan]" + "━" * 88 + "[/]")
            
            # STABILIZATION: Truncate final deliverable content
            truncated_content = _truncate_data(content, max_len=10000)
            content_escaped = str(truncated_content).replace("[", "\\[")
            lines.append(f"[bold yellow]FINAL DELIVERABLE:[/]\n{content_escaped}")
            
            lines.append(f"\n[bold cyan]Artifacts produced:[/] [bold magenta]{artifacts_count}[/]")
            lines.append("[bold cyan]" + "━" * 88 + "[/]")
            console.print("\n".join(lines))
        except Exception as e:
            logger.warning(f"Failed to render final result log: {e}")
