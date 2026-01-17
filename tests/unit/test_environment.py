"""
Tests for environment configuration.
"""

import pytest
import os
from unittest.mock import patch

from shared.environment import (
    EnvironmentMode,
    FeatureFlags,
    EnvironmentConfig,
    get_environment_config,
    set_environment_config,
    is_feature_enabled,
)


class TestEnvironmentMode:
    """Tests for EnvironmentMode enum."""
    
    def test_modes(self):
        """Test environment mode values."""
        assert EnvironmentMode.DEVELOPMENT.value == "development"
        assert EnvironmentMode.STAGING.value == "staging"
        assert EnvironmentMode.PRODUCTION.value == "production"


class TestFeatureFlags:
    """Tests for FeatureFlags."""
    
    def test_default_flags(self):
        """Test default feature flags."""
        flags = FeatureFlags()
        assert flags.enable_multimodal is True
        assert flags.enable_rate_limiting is True
        assert flags.enable_debug_endpoints is False
    
    def test_production_flags(self):
        """Test production feature flags."""
        flags = FeatureFlags.for_production()
        assert flags.enable_semantic_cache is False
        assert flags.enable_debug_endpoints is False
        assert flags.enable_rate_limiting is True
    
    def test_development_flags(self):
        """Test development feature flags."""
        flags = FeatureFlags.for_development()
        assert flags.enable_semantic_cache is True
        assert flags.enable_debug_endpoints is True
    
    def test_staging_flags(self):
        """Test staging feature flags."""
        flags = FeatureFlags.for_staging()
        assert flags.enable_semantic_cache is True
        assert flags.enable_debug_endpoints is False


class TestEnvironmentConfig:
    """Tests for EnvironmentConfig."""
    
    def test_default_config(self):
        """Test default environment config."""
        config = EnvironmentConfig()
        assert config.mode == EnvironmentMode.DEVELOPMENT
        assert config.max_concurrent_requests == 100
    
    def test_production_config(self):
        """Test production environment config."""
        config = EnvironmentConfig.for_production()
        assert config.mode == EnvironmentMode.PRODUCTION
        assert config.max_concurrent_requests == 50
        assert config.log_level == "WARNING"
    
    def test_development_config(self):
        """Test development environment config."""
        config = EnvironmentConfig.for_development()
        assert config.mode == EnvironmentMode.DEVELOPMENT
        assert config.max_concurrent_requests == 200
        assert config.log_level == "DEBUG"
    
    def test_staging_config(self):
        """Test staging environment config."""
        config = EnvironmentConfig.for_staging()
        assert config.mode == EnvironmentMode.STAGING
        assert config.log_level == "INFO"
    
    def test_is_production(self):
        """Test is_production property."""
        prod = EnvironmentConfig.for_production()
        dev = EnvironmentConfig.for_development()
        
        assert prod.is_production is True
        assert dev.is_production is False
    
    def test_is_development(self):
        """Test is_development property."""
        prod = EnvironmentConfig.for_production()
        dev = EnvironmentConfig.for_development()
        
        assert prod.is_development is False
        assert dev.is_development is True
    
    def test_is_staging(self):
        """Test is_staging property."""
        staging = EnvironmentConfig.for_staging()
        
        assert staging.is_staging is True
    
    def test_from_environment_production(self):
        """Test loading production config from environment."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            config = EnvironmentConfig.from_environment()
            assert config.mode == EnvironmentMode.PRODUCTION
    
    def test_from_environment_development(self):
        """Test loading development config from environment."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            config = EnvironmentConfig.from_environment()
            assert config.mode == EnvironmentMode.DEVELOPMENT
    
    def test_from_environment_staging(self):
        """Test loading staging config from environment."""
        with patch.dict(os.environ, {"ENVIRONMENT": "staging"}):
            config = EnvironmentConfig.from_environment()
            assert config.mode == EnvironmentMode.STAGING


class TestIsFeatureEnabled:
    """Tests for is_feature_enabled function."""
    
    def test_check_enabled_feature(self):
        """Test checking enabled feature."""
        config = EnvironmentConfig.for_development()
        set_environment_config(config)
        
        assert is_feature_enabled("multimodal") is True
    
    def test_check_disabled_feature(self):
        """Test checking disabled feature."""
        config = EnvironmentConfig.for_production()
        set_environment_config(config)
        
        assert is_feature_enabled("debug_endpoints") is False
    
    def test_check_nonexistent_feature(self):
        """Test checking non-existent feature."""
        result = is_feature_enabled("nonexistent_feature")
        assert result is False
