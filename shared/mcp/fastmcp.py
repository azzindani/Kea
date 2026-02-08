
import asyncio
import time
import traceback
import inspect
from functools import wraps
from typing import Any, Callable, Dict, Optional, Union, List

import structlog
try:
    from mcp.server.fastmcp import FastMCP as LibFastMCP, Image, Text, Resource
    from pydantic import ValidationError
except ImportError:
    # Fallback for environments where mcp is not installed
    # This ensures the file is at least importable
    class LibFastMCP:
        def __init__(self, name: str, **kwargs): pass
        def tool(self, name: Optional[str] = None, description: Optional[str] = None): 
            def decorator(f): return f
            return decorator
        def add_tool(self, fn: Callable, name: Optional[str] = None, description: Optional[str] = None): pass
        def run(self, transport: str = "stdio"): pass
        def resource(self, uri: str, name: str, description: Optional[str] = None, mime_type: Optional[str] = None):
            def decorator(f): return f
            return decorator
        def prompt(self, name: Optional[str] = None, description: Optional[str] = None):
            def decorator(f): return f
            return decorator
            
    class Image:
        def __init__(self, data: bytes, format: str): 
            self.data = data
            self.format = format

    class Text:
        def __init__(self, text: str): 
            self.text = text

    class Resource:
        def __init__(self, uri: str, name: str, description: Optional[str] = None, mime_type: Optional[str] = None):
            self.uri = uri
            self.name = name
            self.description = description
            self.mime_type = mime_type

    class ValidationError(Exception): pass

logger = structlog.get_logger()

# ==========================================
# 1. Standard Error Constants
# ==========================================
class StandardErrors:
    INPUT_ERROR = "INPUT_ERROR"
    EXECUTION_ERROR = "EXECUTION_ERROR" 
    UPSTREAM_ERROR = "UPSTREAM_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"

# ==========================================
# 2. FastMCP Class (Enhanced Wrapper)
# ==========================================
class FastMCP(LibFastMCP):
    """
    Enhanced MCP Server implementation.
    
    Extends the standard FastMCP to provide:
    1. Input Validation & Sanitization
    2. Reliable Execution (Retries)
    3. Standardized Output Envelope
    4. Structured Error Handling
    """
    
    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)
        self.server_name = name

    def tool(self, name: Optional[str] = None, description: Optional[str] = None):
        """
        Decorator to register a tool with standardized execution wrapper.
        """
        def decorator(func: Callable):
            # 1. Get the original tool name/desc if not provided
            tool_name = name or func.__name__
            tool_desc = description or func.__doc__
            
            # Check if original function is async
            is_async = inspect.iscoroutinefunction(func)

            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                retry_count = 0
                max_retries = 3
                
                # Metadata for the envelope
                meta = {
                    "server": self.server_name,
                    "tool": tool_name,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }

                try:
                    # --- A. INPUT SANITIZATION ---
                    clean_kwargs = {
                        k: v.strip() if isinstance(v, str) else v 
                        for k, v in kwargs.items()
                    }
                    
                    # --- B. EXECUTION WITH RETRY ---
                    last_error = None
                    final_result = None
                    
                    for attempt in range(max_retries):
                        try:
                            # Execute the registered function
                            if is_async:
                                final_result = await func(*args, **clean_kwargs)
                            else:
                                final_result = func(*args, **clean_kwargs)
                            
                            # --- C. STANDARD OUTPUT ---
                            execution_time_ms = (time.perf_counter() - start_time) * 1000
                            meta["duration_ms"] = round(execution_time_ms, 2)
                            meta["retry_count"] = retry_count
                            
                            def json_serial(obj):
                                if hasattr(obj, "model_dump"):
                                    return obj.model_dump()
                                return str(obj)

                            import json
                            return json.dumps({
                                "status": "success",
                                "data": final_result,
                                "meta": meta
                            }, default=json_serial)
                            
                        except (TimeoutError, ConnectionError) as e:
                            # Retryable errors
                            retry_count += 1
                            last_error = e
                            logger.warning(
                                "tool_execution_retry", 
                                tool=tool_name, 
                                attempt=attempt+1, 
                                error=str(e)
                            )
                            await asyncio.sleep(0.5 * (attempt + 1)) # Backoff
                            continue
                            
                        except Exception as e:
                            # Non-retryable error
                            raise e

                    # If we exhausted retries
                    if last_error:
                        raise last_error

                except ValidationError as e:
                    # Pydantic Input Error
                    logger.error("tool_input_error", tool=tool_name, error=str(e))
                    return self._format_error(
                        StandardErrors.INPUT_ERROR, 
                        f"Validation failed: {str(e)}", 
                        meta
                    )

                except Exception as e:
                    # Catch-all for crashes
                    logger.error("tool_execution_failed", tool=tool_name, error=str(e), traceback=traceback.format_exc())
                    error_code = StandardErrors.EXECUTION_ERROR
                    
                    msg = str(e)
                    if "timeout" in msg.lower():
                        error_code = StandardErrors.TIMEOUT_ERROR
                    elif "connection" in msg.lower():
                         error_code = StandardErrors.UPSTREAM_ERROR

                    return self._format_error(
                        error_code, 
                        msg, 
                        meta, 
                        details={"traceback": traceback.format_exc()}
                    )

        return decorator

    def add_tool(self, fn: Callable, name: Optional[str] = None, description: Optional[str] = None):
        """
        Manually register a tool.
        """
        # We use our own tool decorator to ensure the wrapper is applied
        @self.tool(name=name, description=description)
        @wraps(fn)
        async def wrapped_fn(*args, **kwargs):
            if inspect.iscoroutinefunction(fn):
                return await fn(*args, **kwargs)
            return fn(*args, **kwargs)
        
        # We don't need to do anything else as self.tool() already registered it
        return wrapped_fn

    def run(self, transport: str = "stdio"):
        """
        Run the MCP server.
        """
        # If we are using the real LibFastMCP, it will have a run method
        if hasattr(super(), "run"):
            return super().run(transport=transport)
        
        # Fallback/Mock behavior
        logger.info("mcp_server_run_called", server=self.server_name, transport=transport)

    def resource(self, uri: str, name: str, description: Optional[str] = None, mime_type: Optional[str] = None):
        """Proxy for resource decorator."""
        return super().resource(uri, name, description, mime_type)

    def prompt(self, name: Optional[str] = None, description: Optional[str] = None):
        """Proxy for prompt decorator."""
        return super().prompt(name, description)

    def _format_error(self, code: str, message: str, meta: Dict, details: Optional[Dict] = None) -> str:
        """Constructs the standard error envelope."""
        meta["error_code"] = code
        import json
        return json.dumps({
            "status": "error",
            "data": {
                "code": code,
                "message": message,
                "details": details or {}
            },
            "meta": meta
        }, default=str)
