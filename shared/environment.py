"""
Environment Settings (Compatibility Layer).

Provides a bridge between the legacy EnvironmentConfig and the new Settings singleton.
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from shared.config import get_settings

class EnvironmentMode(str, Enum):
    """Environment mode."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class CompatibilityFeatureFlags:
    """Wrapper for FeatureFlags in Settings."""
    def __getattr__(self, name):
        settings = get_settings()
        return getattr(settings.feature_flags, name, False)

@dataclass
class EnvironmentConfig:
    """
    Compatibility wrapper for EnvironmentConfig.
    Maps old fields to the new Settings structure.
    """
    
    @property
    def mode(self) -> EnvironmentMode:
        settings = get_settings()
        return EnvironmentMode(settings.app.environment)
    
    @property
    def features(self) -> CompatibilityFeatureFlags:
        return CompatibilityFeatureFlags()
    
    @property
    def database_url(self) -> str:
        return get_settings().database.url
    
    @property
    def redis_url(self) -> str:
        return get_settings().redis_url
    
    @property
    def max_concurrent_requests(self) -> int:
        return get_settings().api.max_connections
    
    @property
    def log_level(self) -> str:
        return get_settings().logging.level
    
    @property
    def is_production(self) -> bool:
        return self.mode == EnvironmentMode.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        return self.mode == EnvironmentMode.DEVELOPMENT
    
    @property
    def is_staging(self) -> bool:
        return self.mode == EnvironmentMode.STAGING

_config = EnvironmentConfig()

def get_environment_config() -> EnvironmentConfig:
    """Get singleton environment config."""
    return _config

def is_feature_enabled(feature: str) -> bool:
    """Check if a feature is enabled."""
    settings = get_settings()
    return getattr(settings.feature_flags, f"enable_{feature}", False)
