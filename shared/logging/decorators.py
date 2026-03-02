import inspect
import functools
import time
import asyncio
from typing import Any, Callable, Optional

from shared.logging.main import (
    log_input, 
    log_output, 
    log_error, 
    _truncate_data
)

def trace_io(logger_name: Optional[str] = None):
    """
    A unified decorator to standardize input/output logging for any function.
    Automatically captures function name, input arguments (mapped to names), 
    duration, and outputs. Works with both async and sync functions.
    
    Usage:
        @trace_io(logger_name="kernel.planner")
        async def generate_plan(user_id: str, context: dict) -> Plan:
            ...
    """
    def decorator(func: Callable) -> Callable:
        # Resolve the function name or use the override logger_name for source tracking
        source = logger_name or f"{func.__module__}.{func.__qualname__}"
        
        # Capture signature once
        try:
            sig = inspect.signature(func)
        except ValueError:
            sig = None
        
        def _prepare_inputs(*args, **kwargs) -> dict:
            if not sig:
                return {"args": _truncate_data(args), "kwargs": _truncate_data(kwargs)}
                
            try:
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                # Truncate deeply nested or massive inputs to prevent log bloat
                return {k: _truncate_data(v) for k, v in bound.arguments.items() if k != 'self'}
            except Exception:
                # Fallback if binding fails for any tricky args
                return {"args": _truncate_data(args), "kwargs": _truncate_data(kwargs)}

        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                inputs_safe = _prepare_inputs(*args, **kwargs)
                log_input(source=source, data=inputs_safe)
                
                start_time = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    
                    safe_result = _truncate_data(result)
                    log_output(source=source, data={"result": safe_result, "metrics": {"duration_ms": round(duration_ms, 2)}})
                    return result
                except Exception as e:
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    # We pass the metrics inside a dict, which stringifies nicely if log_error explicitly stringifies it, 
                    # but provides all data for JSON serialization.
                    err_payload = {"error": str(e) or e.__class__.__name__, "metrics": {"duration_ms": round(duration_ms, 2)}}
                    log_error(source=source, err=err_payload)
                    raise
            return async_wrapper

        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                inputs_safe = _prepare_inputs(*args, **kwargs)
                log_input(source=source, data=inputs_safe)
                
                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    
                    safe_result = _truncate_data(result)
                    log_output(source=source, data={"result": safe_result, "metrics": {"duration_ms": round(duration_ms, 2)}})
                    return result
                except Exception as e:
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    err_payload = {"error": str(e) or e.__class__.__name__, "metrics": {"duration_ms": round(duration_ms, 2)}}
                    log_error(source=source, err=err_payload)
                    raise
            return sync_wrapper

    return decorator
