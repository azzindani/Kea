"""
Graceful Degradation and Resource-Aware Execution.

Reduces parallelism and load under resource pressure.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, TypeVar

from shared.logging import get_logger


logger = get_logger(__name__)

T = TypeVar("T")


@dataclass
class DegradationLevel:
    """Current degradation level and limits."""
    level: int  # 0=normal, 1=warning, 2=critical
    max_parallel: int
    batch_size: int
    timeout_multiplier: float
    skip_optional_tasks: bool


class GracefulDegrader:
    """
    Manage graceful degradation based on resource pressure.
    
    Integrates with ResourceMonitor to:
    - Reduce parallelism when memory high
    - Increase timeouts when load high
    - Skip optional tasks when critical
    
    Example:
        degrader = GracefulDegrader()
        await degrader.start_monitoring()
        
        # Get current limits
        level = degrader.get_current_level()
        max_workers = level.max_parallel
        
        # Execute with throttle
        async with degrader.throttle():
            await do_work()
    """
    
    def __init__(
        self,
        base_parallel: int = 4,
        base_batch_size: int = 1000,
        base_timeout: float = 30.0,
    ):
        self.base_parallel = base_parallel
        self.base_batch_size = base_batch_size
        self.base_timeout = base_timeout
        
        self._current_level = 0  # 0=normal, 1=warning, 2=critical
        self._monitor = None
        self._semaphore: asyncio.Semaphore | None = None
        
        # Define degradation levels
        self._levels = {
            0: DegradationLevel(
                level=0,
                max_parallel=base_parallel,
                batch_size=base_batch_size,
                timeout_multiplier=1.0,
                skip_optional_tasks=False,
            ),
            1: DegradationLevel(
                level=1,
                max_parallel=max(1, base_parallel // 2),
                batch_size=max(100, base_batch_size // 2),
                timeout_multiplier=1.5,
                skip_optional_tasks=False,
            ),
            2: DegradationLevel(
                level=2,
                max_parallel=1,
                batch_size=max(50, base_batch_size // 4),
                timeout_multiplier=2.0,
                skip_optional_tasks=True,
            ),
        }
        
        self._update_semaphore()
    
    async def start_monitoring(self) -> None:
        """Start resource monitoring."""
        try:
            from shared.hardware import ResourceMonitor, ResourceAlert, AlertLevel
            
            self._monitor = ResourceMonitor()
            self._monitor.on_alert(self._on_alert)
            await self._monitor.start()
            logger.info("Graceful degradation monitoring started")
            
        except ImportError:
            logger.warning("Hardware module not available, degradation disabled")
    
    async def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        if self._monitor:
            await self._monitor.stop()
    
    def get_current_level(self) -> DegradationLevel:
        """Get current degradation level and limits."""
        return self._levels[self._current_level]
    
    def set_level(self, level: int) -> None:
        """Manually set degradation level (0-2)."""
        old_level = self._current_level
        self._current_level = max(0, min(2, level))
        if old_level != self._current_level:
            self._update_semaphore()
            logger.info(f"Degradation level changed: {old_level}   {self._current_level}")
    
    def throttle(self) -> "_ThrottleContext":
        """
        Context manager for throttled execution.
        
        Usage:
            async with degrader.throttle():
                await do_expensive_work()
        """
        return _ThrottleContext(self)
    
    def get_timeout(self, base_timeout: float | None = None) -> float:
        """Get adjusted timeout based on current level."""
        base = base_timeout or self.base_timeout
        return base * self.get_current_level().timeout_multiplier
    
    def should_skip_optional(self) -> bool:
        """Check if optional tasks should be skipped."""
        return self.get_current_level().skip_optional_tasks
    
    def _on_alert(self, alert: "ResourceAlert") -> None:
        """Handle resource alert from monitor."""
        from shared.hardware import AlertLevel
        
        if alert.level == AlertLevel.CRITICAL:
            self.set_level(2)
        elif alert.level == AlertLevel.WARNING:
            if self._current_level < 1:
                self.set_level(1)
        # Gradually recover when resources free up
        elif alert.level == AlertLevel.INFO and self._current_level > 0:
            self.set_level(self._current_level - 1)
    
    def _update_semaphore(self) -> None:
        """Update semaphore to match current level."""
        max_parallel = self.get_current_level().max_parallel
        self._semaphore = asyncio.Semaphore(max_parallel)


class _ThrottleContext:
    """Async context manager for throttled execution."""
    
    def __init__(self, degrader: GracefulDegrader):
        self.degrader = degrader
    
    async def __aenter__(self):
        if self.degrader._semaphore:
            await self.degrader._semaphore.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.degrader._semaphore:
            self.degrader._semaphore.release()
        return False


def throttled(degrader: GracefulDegrader | None = None):
    """
    Decorator for throttled async functions.
    
    Usage:
        @throttled(my_degrader)
        async def expensive_operation():
            ...
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if degrader:
                async with degrader.throttle():
                    return await func(*args, **kwargs)
            else:
                return await func(*args, **kwargs)
        return wrapper
    return decorator


# Global instance
_degrader: GracefulDegrader | None = None


def get_degrader() -> GracefulDegrader:
    """Get or create global degrader."""
    global _degrader
    if _degrader is None:
        _degrader = GracefulDegrader()
    return _degrader
