"""
Database Package.

Provides connection pool, health checks, and migrations.
"""

from shared.database.connection import (
    DatabasePool,
    DatabaseConfig,
    get_database_pool,
    close_database_pool,
)
from shared.database.health import (
    HealthChecker,
    HealthStatus,
    SystemHealth,
    get_health_checker,
)

__all__ = [
    "DatabasePool",
    "DatabaseConfig",
    "get_database_pool",
    "close_database_pool",
    "HealthChecker",
    "HealthStatus",
    "SystemHealth",
    "get_health_checker",
]
