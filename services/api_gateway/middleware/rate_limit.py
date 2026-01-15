"""
Rate Limiting Middleware.

Production-ready rate limiting with:
- Per-user/IP limits
- Sliding window algorithm
- Redis-backed for distributed deployments
- Fallback to in-memory for single instance
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from shared.logging import get_logger
from shared.environment import get_environment_config


logger = get_logger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10
    
    # Exempt paths
    exempt_paths: list[str] = field(default_factory=lambda: [
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/metrics",
    ])
    
    @classmethod
    def from_environment(cls) -> "RateLimitConfig":
        """Create config from environment."""
        env_config = get_environment_config()
        return cls(
            requests_per_minute=env_config.rate_limit_per_minute,
            requests_per_hour=env_config.rate_limit_per_minute * 60,
            burst_size=min(env_config.rate_limit_per_minute // 2, 20),
        )


class SlidingWindowCounter:
    """Sliding window rate limiter - in memory."""
    
    def __init__(self):
        self._windows: dict[str, list[float]] = defaultdict(list)
        self._last_cleanup = time.time()
    
    def is_allowed(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60,
    ) -> tuple[bool, int]:
        """
        Check if request is allowed.
        
        Returns:
            (allowed, remaining_requests)
        """
        now = time.time()
        window_start = now - window_seconds
        
        # Cleanup old entries periodically
        if now - self._last_cleanup > 60:
            self._cleanup(window_start)
        
        # Get requests in current window
        requests = self._windows[key]
        requests = [t for t in requests if t > window_start]
        self._windows[key] = requests
        
        if len(requests) >= limit:
            return False, 0
        
        # Add current request
        requests.append(now)
        remaining = limit - len(requests)
        
        return True, remaining
    
    def _cleanup(self, cutoff: float):
        """Remove old entries."""
        self._last_cleanup = time.time()
        keys_to_delete = []
        
        for key, requests in self._windows.items():
            self._windows[key] = [t for t in requests if t > cutoff]
            if not self._windows[key]:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self._windows[key]


class RedisRateLimiter:
    """Redis-backed rate limiter for distributed deployments."""
    
    def __init__(self, redis_url: str = None):
        self._redis = None
        self._redis_url = redis_url
    
    async def _get_client(self):
        """Get Redis client lazily."""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(
                    self._redis_url or "redis://localhost:6379",
                    decode_responses=True,
                )
            except Exception as e:
                logger.warning(f"Redis not available: {e}")
                return None
        return self._redis
    
    async def is_allowed(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60,
    ) -> tuple[bool, int]:
        """Check if request is allowed using Redis."""
        client = await self._get_client()
        if not client:
            return True, limit  # Fail open if Redis unavailable
        
        try:
            pipe = client.pipeline()
            now = time.time()
            window_key = f"ratelimit:{key}"
            
            pipe.zremrangebyscore(window_key, 0, now - window_seconds)
            pipe.zadd(window_key, {str(now): now})
            pipe.zcard(window_key)
            pipe.expire(window_key, window_seconds)
            
            results = await pipe.execute()
            count = results[2]
            
            if count > limit:
                return False, 0
            
            return True, limit - count
            
        except Exception as e:
            logger.warning(f"Redis rate limit error: {e}")
            return True, limit  # Fail open


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.
    
    Uses Redis in production, in-memory for development.
    """
    
    def __init__(self, app, config: RateLimitConfig = None):
        super().__init__(app)
        self.config = config or RateLimitConfig.from_environment()
        self._memory_limiter = SlidingWindowCounter()
        self._redis_limiter: RedisRateLimiter | None = None
        
        env_config = get_environment_config()
        if env_config.is_production:
            self._redis_limiter = RedisRateLimiter()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        
        # Skip exempt paths
        if any(request.url.path.startswith(p) for p in self.config.exempt_paths):
            return await call_next(request)
        
        # Get rate limit key
        key = self._get_key(request)
        
        # Check rate limit
        if self._redis_limiter:
            allowed, remaining = await self._redis_limiter.is_allowed(
                key,
                self.config.requests_per_minute,
                60,
            )
        else:
            allowed, remaining = self._memory_limiter.is_allowed(
                key,
                self.config.requests_per_minute,
                60,
            )
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for {key}")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.config.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                },
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.config.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response
    
    def _get_key(self, request: Request) -> str:
        """Get rate limit key for request."""
        # Use user ID if authenticated
        user = getattr(request.state, "user", None)
        if user and hasattr(user, "user_id") and user.user_id != "anonymous":
            return f"user:{user.user_id}"
        
        # Fall back to IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip:{ip}"
