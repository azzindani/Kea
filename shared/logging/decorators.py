"""
Logging Decorators.

Provides decorators for automatic function logging.
"""

from __future__ import annotations

import functools
import time
from typing import Any, Callable, TypeVar, ParamSpec

from shared.logging.structured import get_logger
from shared.logging.context import get_context

P = ParamSpec("P")
T = TypeVar("T")


def log_execution(
    logger_name: str | None = None,
    log_args: bool = True,
    log_result: bool = False,
    log_timing: bool = True,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for logging function execution.
    
    Args:
        logger_name: Logger name (defaults to function module)
        log_args: Whether to log function arguments
        log_result: Whether to log return value
        log_timing: Whether to log execution time
        
    Example:
        @log_execution(log_timing=True)
        async def fetch_data(url: str) -> dict:
            ...
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        logger = get_logger(logger_name or func.__module__)
        
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            ctx = get_context()
            func_name = func.__name__
            
            # Log start
            extra: dict[str, Any] = {"function": func_name}
            if log_args:
                extra["args"] = str(args)[:200]
                extra["kwargs"] = {k: str(v)[:100] for k, v in kwargs.items()}
            
            logger.info(f"Starting {func_name}", extra=extra)
            
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                
                # Log success
                extra = {"function": func_name, "status": "success"}
                if log_timing:
                    extra["duration_ms"] = round((time.perf_counter() - start_time) * 1000, 2)
                if log_result:
                    extra["result"] = str(result)[:200]
                
                logger.info(f"Completed {func_name}", extra=extra)
                return result
                
            except Exception as e:
                # Log error
                extra = {
                    "function": func_name,
                    "status": "error",
                    "error": str(e),
                }
                if log_timing:
                    extra["duration_ms"] = round((time.perf_counter() - start_time) * 1000, 2)
                
                logger.error(f"Failed {func_name}", extra=extra, exc_info=True)
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            logger = get_logger(logger_name or func.__module__)
            func_name = func.__name__
            
            extra: dict[str, Any] = {"function": func_name}
            if log_args:
                extra["args"] = str(args)[:200]
                extra["kwargs"] = {k: str(v)[:100] for k, v in kwargs.items()}
            
            logger.info(f"Starting {func_name}", extra=extra)
            
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                
                extra = {"function": func_name, "status": "success"}
                if log_timing:
                    extra["duration_ms"] = round((time.perf_counter() - start_time) * 1000, 2)
                if log_result:
                    extra["result"] = str(result)[:200]
                
                logger.info(f"Completed {func_name}", extra=extra)
                return result
                
            except Exception as e:
                extra = {
                    "function": func_name,
                    "status": "error",
                    "error": str(e),
                }
                if log_timing:
                    extra["duration_ms"] = round((time.perf_counter() - start_time) * 1000, 2)
                
                logger.error(f"Failed {func_name}", extra=extra, exc_info=True)
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore
    
    return decorator
