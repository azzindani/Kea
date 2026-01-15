"""
Unit Tests: Database Pool and Health Checks.

Tests for database connection pool and health checker.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from shared.database.connection import (
    DatabaseConfig,
    DatabasePool,
)
from shared.database.health import (
    HealthChecker,
    HealthStatus,
    SystemHealth,
)


class TestDatabaseConfig:
    """Test database configuration."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = DatabaseConfig(url="postgresql://localhost/test")
        
        assert config.min_connections == 2
        assert config.max_connections == 10
        assert config.connection_timeout == 30.0
    
    def test_production_config(self):
        """Test production configuration settings."""
        with patch("shared.database.connection.get_environment_config") as mock:
            mock.return_value.is_production = True
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://prod/db"}):
                config = DatabaseConfig.from_environment()
                
                assert config.min_connections == 5
                assert config.max_connections == 20
    
    def test_development_config(self):
        """Test development configuration settings."""
        with patch("shared.database.connection.get_environment_config") as mock:
            mock.return_value.is_production = False
            
            config = DatabaseConfig.from_environment()
            
            assert config.min_connections == 1
            assert config.max_connections == 5


class TestDatabasePool:
    """Test database connection pool."""
    
    def test_pool_initialization(self):
        """Test pool initializes correctly."""
        pool = DatabasePool(DatabaseConfig(url="sqlite:///test.db"))
        
        assert pool._is_initialized is False
        assert pool._is_postgres is False
    
    def test_postgres_detection(self):
        """Test PostgreSQL URL detection."""
        pool = DatabasePool(DatabaseConfig(url="postgresql://localhost/test"))
        
        assert pool._is_postgres is True
    
    def test_sqlite_detection(self):
        """Test SQLite URL detection."""
        pool = DatabasePool(DatabaseConfig(url="sqlite:///data/test.db"))
        
        assert pool._is_postgres is False


class TestHealthStatus:
    """Test health status model."""
    
    def test_healthy_status(self):
        """Test healthy status creation."""
        status = HealthStatus(
            service="test",
            status="healthy",
            latency_ms=5.0,
        )
        
        assert status.service == "test"
        assert status.status == "healthy"
        assert status.latency_ms == 5.0
    
    def test_unhealthy_status(self):
        """Test unhealthy status creation."""
        status = HealthStatus(
            service="database",
            status="unhealthy",
            details={"error": "Connection refused"},
        )
        
        assert status.status == "unhealthy"
        assert "error" in status.details


class TestSystemHealth:
    """Test system health aggregate."""
    
    def test_all_healthy(self):
        """Test overall healthy when all checks pass."""
        checks = [
            HealthStatus(service="db", status="healthy"),
            HealthStatus(service="redis", status="healthy"),
        ]
        
        health = SystemHealth(status="healthy", checks=checks)
        
        assert health.status == "healthy"
    
    def test_to_dict(self):
        """Test dictionary serialization."""
        checks = [
            HealthStatus(service="db", status="healthy", latency_ms=5.0),
        ]
        
        health = SystemHealth(status="healthy", checks=checks)
        result = health.to_dict()
        
        assert result["status"] == "healthy"
        assert "db" in result["checks"]
        assert result["checks"]["db"]["latency_ms"] == 5.0


class TestHealthChecker:
    """Test health checker."""
    
    @pytest.fixture
    def checker(self):
        return HealthChecker()
    
    @pytest.mark.asyncio
    async def test_check_memory(self, checker):
        """Test memory check returns valid status."""
        with patch("shared.database.health.psutil") as mock_psutil:
            mock_psutil.virtual_memory.return_value = MagicMock(
                percent=50.0,
                available=8 * 1024**3,
                total=16 * 1024**3,
            )
            
            result = await checker.check_memory()
            
            assert result.service == "memory"
            assert result.status == "healthy"
            assert result.details["used_percent"] == 50.0
    
    @pytest.mark.asyncio
    async def test_check_memory_warning(self, checker):
        """Test memory warning at high usage."""
        with patch("shared.database.health.psutil") as mock_psutil:
            mock_psutil.virtual_memory.return_value = MagicMock(
                percent=85.0,
                available=2 * 1024**3,
                total=16 * 1024**3,
            )
            
            result = await checker.check_memory()
            
            assert result.status == "degraded"
    
    @pytest.mark.asyncio
    async def test_check_database_failure(self, checker):
        """Test database check handles failure."""
        with patch("shared.database.health.get_database_pool") as mock:
            mock.side_effect = Exception("Connection refused")
            
            result = await checker.check_database()
            
            assert result.service == "database"
            assert result.status == "unhealthy"
            assert "error" in result.details
