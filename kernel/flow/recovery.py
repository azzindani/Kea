"""
Error Recovery with Retry and Backoff.

Provides automatic retry, circuit breaker, and error classification.
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, TypeVar

from shared.logging import get_logger


logger = get_logger(__name__)

T = TypeVar("T")


class ErrorType(str, Enum):
    """Classification of errors for recovery strategy."""
    TRANSIENT = "transient"      # Retry after delay (network, rate limit)
    PERMANENT = "permanent"      # Don't retry (invalid input, auth failed)
    RESOURCE = "resource"        # Wait for resource (memory, disk)
    TIMEOUT = "timeout"          # Increase timeout and retry
    UNKNOWN = "unknown"          # Conservative retry


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay: float = 1.0          # seconds
    max_delay: float = 60.0          # seconds
    exponential_base: float = 2.0
    jitter: bool = True              # Add randomness to delay
    retry_on: tuple[type[Exception], ...] = (Exception,)
    dont_retry_on: tuple[type[Exception], ...] = (KeyboardInterrupt, SystemExit)


@dataclass
class RetryState:
    """State tracking for retries."""
    attempts: int = 0
    last_error: Exception | None = None
    last_attempt: datetime | None = None
    total_delay: float = 0.0


def classify_error(error: Exception) -> ErrorType:
    """Classify error for recovery strategy."""
    error_msg = str(error).lower()
    error_type = type(error).__name__.lower()
    
    # Rate limit / throttling
    if any(kw in error_msg for kw in ["rate limit", "429", "throttl", "too many"]):
        return ErrorType.TRANSIENT
    
    # Network issues
    if any(kw in error_type for kw in ["connection", "timeout", "network", "socket"]):
        return ErrorType.TRANSIENT
    
    # Resource issues
    if any(kw in error_msg for kw in ["memory", "disk", "space", "resource"]):
        return ErrorType.RESOURCE
    
    # Timeout
    if "timeout" in error_msg or "timed out" in error_msg:
        return ErrorType.TIMEOUT
    
    # Auth / permission
    if any(kw in error_msg for kw in ["auth", "forbidden", "401", "403", "permission"]):
        return ErrorType.PERMANENT
    
    # Validation
    if any(kw in error_msg for kw in ["invalid", "validation", "required", "missing"]):
        return ErrorType.PERMANENT
    
    return ErrorType.UNKNOWN


def calculate_delay(attempt: int, config: RetryConfig, error_type: ErrorType) -> float:
    """Calculate delay before next retry."""
    # Base exponential backoff
    delay = config.base_delay * (config.exponential_base ** attempt)
    
    # Adjust based on error type
    if error_type == ErrorType.TIMEOUT:
        delay *= 1.5  # Longer wait for timeouts
    elif error_type == ErrorType.RESOURCE:
        delay *= 2.0  # Even longer for resource issues
    
    # Apply jitter
    if config.jitter:
        delay *= (0.5 + random.random())  # 50-150% of calculated delay
    
    # Cap at max delay
    return min(delay, config.max_delay)


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    on_error: Callable[[Exception, int], None] | None = None,
):
    """
    Decorator for automatic retry with exponential backoff.
    
    Usage:
        @retry(max_attempts=3, base_delay=1.0)
        async def fetch_data(url: str) -> dict:
            ...
        
        @retry(max_attempts=5, on_error=lambda e, n: logger.warning(f"Retry {n}: {e}"))
        async def risky_operation():
            ...
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter,
    )
    
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            state = RetryState()
            
            while state.attempts < config.max_attempts:
                try:
                    state.last_attempt = datetime.utcnow()
                    return await func(*args, **kwargs)
                    
                except config.dont_retry_on:
                    raise
                    
                except config.retry_on as e:
                    state.attempts += 1
                    state.last_error = e
                    error_type = classify_error(e)
                    
                    # Don't retry permanent errors
                    if error_type == ErrorType.PERMANENT:
                        logger.warning(f"{func.__name__} failed with permanent error: {e}")
                        raise
                    
                    # Check if we have retries left
                    if state.attempts >= config.max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {state.attempts} attempts: {e}"
                        )
                        raise
                    
                    # Calculate and apply delay
                    delay = calculate_delay(state.attempts - 1, config, error_type)
                    state.total_delay += delay
                    
                    logger.warning(
                        f"{func.__name__} attempt {state.attempts} failed ({error_type.value}): {e}. "
                        f"Retrying in {delay:.1f}s"
                    )
                    
                    if on_error:
                        on_error(e, state.attempts)
                    
                    await asyncio.sleep(delay)
            
            # Should not reach here, but just in case
            raise state.last_error if state.last_error else RuntimeError("Retry exhausted")
        
        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failing, reject requests immediately
    - HALF_OPEN: Testing, allow limited requests
    
    Example:
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        
        async with breaker:
            await risky_operation()
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_requests: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_requests = half_open_requests
        
        self._failures = 0
        self._successes = 0
        self._state = "closed"
        self._last_failure: datetime | None = None
        self._half_open_count = 0
    
    @property
    def state(self) -> str:
        """Get current circuit state."""
        if self._state == "open":
            # Check if recovery timeout has passed
            if self._last_failure:
                elapsed = (datetime.utcnow() - self._last_failure).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self._state = "half_open"
                    self._half_open_count = 0
        return self._state
    
    def record_success(self) -> None:
        """Record successful request."""
        self._successes += 1
        if self.state == "half_open":
            self._half_open_count += 1
            if self._half_open_count >= self.half_open_requests:
                self._state = "closed"
                self._failures = 0
                logger.info("Circuit breaker closed (recovered)")
    
    def record_failure(self, error: Exception) -> None:
        """Record failed request."""
        self._failures += 1
        self._last_failure = datetime.utcnow()
        
        if self._failures >= self.failure_threshold:
            self._state = "open"
            logger.warning(
                f"Circuit breaker opened after {self._failures} failures"
            )
    
    async def __aenter__(self):
        if self.state == "open":
            raise CircuitOpenError(
                f"Circuit breaker open, retry after {self.recovery_timeout}s"
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.record_success()
        elif exc_val:
            self.record_failure(exc_val)
        return False


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


# Convenience decorators
def with_circuit_breaker(breaker: CircuitBreaker):
    """Decorator to wrap function with circuit breaker."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with breaker:
                return await func(*args, **kwargs)
        return wrapper
    return decorator


# Global circuit breakers for common services
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str) -> CircuitBreaker:
    """Get or create named circuit breaker."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker()
    return _circuit_breakers[name]
