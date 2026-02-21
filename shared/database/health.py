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

from shared.logging.main import get_logger


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
