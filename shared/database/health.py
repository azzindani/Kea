"""
Health Check Module.

Comprehensive health checks for all dependencies.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from shared.logging import get_logger


logger = get_logger(__name__)


@dataclass
class HealthStatus:
    """Health check result."""
    service: str
    status: str  # healthy, degraded, unhealthy
    latency_ms: float = 0.0
    details: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class SystemHealth:
    """Overall system health."""
    status: str  # healthy, degraded, unhealthy
    checks: list[HealthStatus] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "timestamp": self.timestamp,
            "checks": {
                c.service: {
                    "status": c.status,
                    "latency_ms": c.latency_ms,
                    **c.details,
                }
                for c in self.checks
            },
        }


class HealthChecker:
    """
    Comprehensive health checker.
    
    Checks:
    - Database (PostgreSQL/SQLite)
    - Redis cache
    - Vector DB (Qdrant)
    - Memory usage
    """
    
    async def check_all(self) -> SystemHealth:
        """Run all health checks."""
        checks = await asyncio.gather(
            self.check_database(),
            self.check_redis(),
            self.check_qdrant(),
            self.check_memory(),
            return_exceptions=True,
        )
        
        # Handle exceptions
        results = []
        for check in checks:
            if isinstance(check, Exception):
                results.append(HealthStatus(
                    service="unknown",
                    status="unhealthy",
                    details={"error": str(check)},
                ))
            else:
                results.append(check)
        
        # Determine overall status
        statuses = [c.status for c in results]
        if all(s == "healthy" for s in statuses):
            overall = "healthy"
        elif any(s == "unhealthy" for s in statuses):
            overall = "unhealthy"
        else:
            overall = "degraded"
        
        return SystemHealth(status=overall, checks=results)
    
    async def check_database(self) -> HealthStatus:
        """Check database connectivity."""
        start = time.time()
        
        try:
            from shared.database.connection import get_database_pool
            
            pool = await get_database_pool()
            result = await pool.health_check()
            
            latency = (time.time() - start) * 1000
            
            return HealthStatus(
                service="database",
                status=result.get("status", "unhealthy"),
                latency_ms=latency,
                details=result,
            )
            
        except Exception as e:
            return HealthStatus(
                service="database",
                status="unhealthy",
                latency_ms=(time.time() - start) * 1000,
                details={"error": str(e)},
            )
    
    async def check_redis(self) -> HealthStatus:
        """Check Redis connectivity."""
        start = time.time()
        
        try:
            import os
            redis_url = os.getenv("REDIS_URL")
            
            if not redis_url:
                return HealthStatus(
                    service="redis",
                    status="degraded",
                    details={"message": "Redis not configured"},
                )
            
            import redis.asyncio as redis_lib
            
            client = redis_lib.from_url(redis_url)
            await client.ping()
            info = await client.info("memory")
            await client.close()
            
            latency = (time.time() - start) * 1000
            
            return HealthStatus(
                service="redis",
                status="healthy",
                latency_ms=latency,
                details={
                    "used_memory_human": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients"),
                },
            )
            
        except ImportError:
            return HealthStatus(
                service="redis",
                status="degraded",
                details={"message": "redis package not installed"},
            )
        except Exception as e:
            return HealthStatus(
                service="redis",
                status="unhealthy",
                latency_ms=(time.time() - start) * 1000,
                details={"error": str(e)},
            )
    
    async def check_qdrant(self) -> HealthStatus:
        """Check Qdrant vector DB connectivity."""
        start = time.time()
        
        try:
            import os
            import httpx
            
            qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{qdrant_url}/healthz")
                
                latency = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    return HealthStatus(
                        service="qdrant",
                        status="healthy",
                        latency_ms=latency,
                    )
                else:
                    return HealthStatus(
                        service="qdrant",
                        status="unhealthy",
                        latency_ms=latency,
                        details={"status_code": response.status_code},
                    )
            
        except Exception as e:
            return HealthStatus(
                service="qdrant",
                status="unhealthy",
                latency_ms=(time.time() - start) * 1000,
                details={"error": str(e)},
            )
    
    async def check_memory(self) -> HealthStatus:
        """Check memory usage."""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            
            # Warn if over 80% usage
            if memory.percent > 90:
                status = "unhealthy"
            elif memory.percent > 80:
                status = "degraded"
            else:
                status = "healthy"
            
            return HealthStatus(
                service="memory",
                status=status,
                details={
                    "used_percent": memory.percent,
                    "available_gb": round(memory.available / (1024**3), 2),
                    "total_gb": round(memory.total / (1024**3), 2),
                },
            )
            
        except ImportError:
            return HealthStatus(
                service="memory",
                status="degraded",
                details={"message": "psutil not installed"},
            )


# Singleton
_health_checker: HealthChecker | None = None


def get_health_checker() -> HealthChecker:
    """Get singleton health checker."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker
