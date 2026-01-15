"""
Unit Tests: Environment Configuration.

Tests for environment detection and feature flags.
"""

import pytest
import os
from unittest.mock import patch

from shared.environment import (
    Environment,
    EnvironmentConfig,
    get_environment_config,
)


class TestEnvironment:
    """Test environment enum."""
    
    def test_development(self):
        """Test development environment."""
        env = Environment.DEVELOPMENT
        assert env.value == "development"
    
    def test_staging(self):
        """Test staging environment."""
        env = Environment.STAGING
        assert env.value == "staging"
    
    def test_production(self):
        """Test production environment."""
        env = Environment.PRODUCTION
        assert env.value == "production"


class TestEnvironmentConfig:
    """Test environment configuration."""
    
    def test_development_defaults(self):
        """Test development environment defaults."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False):
            config = EnvironmentConfig.create()
            
            assert config.environment == Environment.DEVELOPMENT
            assert config.is_development is True
            assert config.is_production is False
            assert config.debug is True
    
    def test_production_defaults(self):
        """Test production environment defaults."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=False):
            config = EnvironmentConfig.create()
            
            assert config.environment == Environment.PRODUCTION
            assert config.is_production is True
            assert config.is_development is False
            assert config.debug is False
    
    def test_staging_defaults(self):
        """Test staging environment defaults."""
        with patch.dict(os.environ, {"ENVIRONMENT": "staging"}, clear=False):
            config = EnvironmentConfig.create()
            
            assert config.environment == Environment.STAGING
            assert config.is_staging is True
    
    def test_feature_flags_development(self):
        """Test feature flags in development."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False):
            config = EnvironmentConfig.create()
            
            # Development should have relaxed limits
            assert config.rate_limit_per_minute >= 60
            assert config.enable_docs is True
    
    def test_feature_flags_production(self):
        """Test feature flags in production."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=False):
            config = EnvironmentConfig.create()
            
            # Production should be stricter
            assert config.enable_docs is False  # API docs disabled
    
    def test_log_level_development(self):
        """Test log level in development."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False):
            config = EnvironmentConfig.create()
            
            assert config.log_level == "DEBUG"
    
    def test_log_level_production(self):
        """Test log level in production."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=False):
            config = EnvironmentConfig.create()
            
            assert config.log_level == "WARNING"
    
    def test_custom_env_var_override(self):
        """Test custom environment variable override."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "LOG_LEVEL": "ERROR",
        }, clear=False):
            config = EnvironmentConfig.create()
            
            assert config.log_level == "ERROR"


class TestGetEnvironmentConfig:
    """Test singleton getter."""
    
    def test_returns_config(self):
        """Test config is returned."""
        config = get_environment_config()
        
        assert config is not None
        assert isinstance(config, EnvironmentConfig)
    
    def test_caches_config(self):
        """Test config is cached (same instance)."""
        config1 = get_environment_config()
        config2 = get_environment_config()
        
        assert config1 is config2


class TestDatabaseURL:
    """Test database URL handling."""
    
    def test_development_uses_sqlite(self):
        """Test development uses SQLite by default."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False):
            config = EnvironmentConfig.create()
            
            assert "sqlite" in config.database_url.lower()
    
    def test_production_requires_postgres(self):
        """Test production requires PostgreSQL."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
        }, clear=False):
            config = EnvironmentConfig.create()
            
            assert "postgresql" in config.database_url.lower()


class TestSecretValidation:
    """Test secret validation."""
    
    def test_production_requires_jwt_secret(self):
        """Test production requires JWT secret."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": "",
        }, clear=False):
            with pytest.raises(ValueError, match="JWT_SECRET"):
                config = EnvironmentConfig.create()
                config.validate_production()
    
    def test_jwt_secret_minimum_length(self):
        """Test JWT secret minimum length."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": "short",
        }, clear=False):
            with pytest.raises(ValueError):
                config = EnvironmentConfig.create()
                config.validate_production()
