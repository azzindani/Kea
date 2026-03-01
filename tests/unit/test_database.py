"""
Tests for database health checks and connection pool.
"""


import pytest


class TestHealthStatus:
    """Tests for HealthStatus dataclass."""

    def test_import_health_status(self):
        """Test that HealthStatus can be imported."""
        from shared.database.health import HealthStatus
        assert HealthStatus is not None

    def test_create_health_status(self):
        """Test creating health status."""
        from shared.database.health import HealthStatus

        status = HealthStatus(
            service="database",
            status="healthy",
            latency_ms=5.0,
        )

        assert status.service == "database"
        assert status.status == "healthy"
        assert status.latency_ms == 5.0


class TestSystemHealth:
    """Tests for SystemHealth dataclass."""

    def test_import_system_health(self):
        """Test that SystemHealth can be imported."""
        from shared.database.health import SystemHealth
        assert SystemHealth is not None

    def test_to_dict(self):
        """Test to_dict method."""
        from shared.database.health import HealthStatus, SystemHealth

        system = SystemHealth(
            status="healthy",
            checks=[
                HealthStatus(service="db", status="healthy"),
            ]
        )

        result = system.to_dict()
        assert result["status"] == "healthy"
        assert "db" in result["checks"]


class TestHealthChecker:
    """Tests for HealthChecker."""

    def test_import_health_checker(self):
        """Test that HealthChecker can be imported."""
        from shared.database.health import HealthChecker, get_health_checker
        assert HealthChecker is not None
        assert get_health_checker is not None

    def test_create_health_checker(self):
        """Test creating health checker."""
        from shared.database.health import HealthChecker
        checker = HealthChecker()
        assert checker is not None

    @pytest.mark.asyncio
    async def test_check_memory(self):
        """Test check_memory method."""
        from shared.database.health import HealthChecker

        checker = HealthChecker()
        result = await checker.check_memory()

        assert result.service == "memory"
        assert result.status in ["healthy", "degraded", "unhealthy"]

    @pytest.mark.asyncio
    async def test_check_database(self):
        """Test check_database method."""
        from shared.database.health import HealthChecker

        checker = HealthChecker()
        result = await checker.check_database()

        assert result.service == "database"
        assert result.status in ["healthy", "degraded", "unhealthy"]

    @pytest.mark.asyncio
    async def test_check_all(self):
        """Test check_all method."""
        from shared.database.health import HealthChecker

        checker = HealthChecker()
        result = await checker.check_all()

        assert result.status in ["healthy", "degraded", "unhealthy"]
        assert len(result.checks) > 0


class TestDatabasePool:
    """Tests for database pool."""

    def test_import_database_pool(self):
        """Test that database pool can be imported."""
        from shared.database.connection import (
            get_database_pool,
        )
        assert get_database_pool is not None

    @pytest.mark.asyncio
    async def test_get_database_pool(self):
        """Test getting database pool."""
        from shared.database.connection import get_database_pool

        pool = await get_database_pool()
        assert pool is not None

    @pytest.mark.asyncio
    async def test_pool_health_check(self):
        """Test pool health check."""
        from shared.database.connection import get_database_pool

        pool = await get_database_pool()
        result = await pool.health_check()

        assert "status" in result
