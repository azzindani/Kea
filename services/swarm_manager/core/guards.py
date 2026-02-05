"""
Resource Guards for System Protection.

Prevents runaway agents, memory exhaustion, and tool abuse.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from shared.logging import get_logger


logger = get_logger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    max_per_minute: int = 100
    window_seconds: float = 60.0


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, max_per_minute: int = 100):
        self.max_per_minute = max_per_minute
        self._tokens: dict[str, list[float]] = {}
    
    def check(self, key: str) -> bool:
        """Check if request is allowed."""
        now = time.time()
        window_start = now - 60.0
        
        if key not in self._tokens:
            self._tokens[key] = []
        
        # Remove old tokens
        self._tokens[key] = [t for t in self._tokens[key] if t > window_start]
        
        # Check limit
        if len(self._tokens[key]) >= self.max_per_minute:
            return False
        
        self._tokens[key].append(now)
        return True
    
    def get_remaining(self, key: str) -> int:
        """Get remaining quota for key."""
        now = time.time()
        window_start = now - 60.0
        
        if key not in self._tokens:
            return self.max_per_minute
        
        recent = [t for t in self._tokens[key] if t > window_start]
        return max(0, self.max_per_minute - len(recent))


class ResourceGuard:
    """
    Prevent system collapse from runaway agents.
    
    Guards against:
    - Too many agents spawned
    - Memory exhaustion
    - Tool call flooding
    
    Example:
        guard = ResourceGuard()
        
        if await guard.check_can_spawn():
            # Safe to spawn agent
        else:
            # At limit, wait or degrade
    """
    
    def __init__(
        self,
        max_agents_per_minute: int = 100,
        max_memory_percent: float = 85.0,
        max_tool_calls_per_minute: int = 100,
    ):
        self.max_agents_per_minute = max_agents_per_minute
        self.max_memory_percent = max_memory_percent
        self.max_tool_calls_per_minute = max_tool_calls_per_minute
        
        self._agent_limiter = RateLimiter(max_agents_per_minute)
        self._tool_limiter = RateLimiter(max_tool_calls_per_minute)
        self._active_agents = 0
    
    async def check_can_spawn(self, session_id: str = "default") -> bool:
        """Check if spawning a new agent is allowed."""
        if not self._agent_limiter.check(session_id):
            logger.warning(f"Agent spawn rate limit reached for {session_id}")
            return False
        
        if not await self.check_memory_ok():
            return False
        
        return True
    
    async def check_memory_ok(self) -> bool:
        """Check if memory usage is acceptable."""
        try:
            from shared.hardware import detect_hardware
            profile = detect_hardware()
            pressure = profile.memory_pressure() * 100
            
            if pressure > self.max_memory_percent:
                logger.warning(f"Memory pressure too high: {pressure:.1f}%")
                return False
            return True
        except Exception:
            # If we can't detect, assume OK
            return True
    
    def check_tool_quota(self, tool_category: str) -> bool:
        """Check if tool calls are within quota."""
        return self._tool_limiter.check(tool_category)
    
    def register_agent_spawn(self) -> None:
        """Track agent spawn."""
        self._active_agents += 1
        logger.debug(f"Active agents: {self._active_agents}")
    
    def register_agent_complete(self) -> None:
        """Track agent completion."""
        self._active_agents = max(0, self._active_agents - 1)
    
    @property
    def active_agent_count(self) -> int:
        """Get current active agent count."""
        return self._active_agents


# Global instance
_guard: ResourceGuard | None = None


def get_resource_guard() -> ResourceGuard:
    """Get or create global resource guard."""
    global _guard
    if _guard is None:
        _guard = ResourceGuard()
    return _guard
