"""
Environment Settings.

Provides dev/production separation with feature flags.
Production mode = most stable, conservative settings.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from shared.logging import get_logger


logger = get_logger(__name__)


class EnvironmentMode(Enum):
    """Environment mode."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class FeatureFlags:
    """
    Feature flags for controlling experimental vs stable features.
    
    Production mode enforces stable features only.
    Development mode allows all features.
    """
    
    # Core Features
    enable_multimodal: bool = True          # v0.4.0 modality support
    enable_query_classifier: bool = True     # v0.4.0 query classification
    enable_compliance_check: bool = True     # v0.4.0 compliance engine
    enable_audit_trail: bool = True          # v0.4.0 audit logging
    enable_context_cache: bool = True        # v0.4.0 caching
    
    # Experimental Features (dev/staging only)
    enable_semantic_cache: bool = False      # Semantic similarity matching
    enable_agent_swarm: bool = False         # Multi-agent spawning
    enable_curiosity_engine: bool = False    # Auto question generation
    
    # Safety Features (always on in production)
    enable_rate_limiting: bool = True
    enable_input_validation: bool = True
    enable_output_sanitization: bool = True
    
    # Debug Features (never in production)
    enable_debug_endpoints: bool = False
    enable_verbose_logging: bool = False
    enable_mock_responses: bool = False
    
    @classmethod
    def for_production(cls) -> "FeatureFlags":
        """Get production-safe feature flags."""
        return cls(
            # Stable features only
            enable_multimodal=True,
            enable_query_classifier=True,
            enable_compliance_check=True,
            enable_audit_trail=True,
            enable_context_cache=True,
            # Experimental OFF
            enable_semantic_cache=False,
            enable_agent_swarm=False,
            enable_curiosity_engine=False,
            # Safety ON
            enable_rate_limiting=True,
            enable_input_validation=True,
            enable_output_sanitization=True,
            # Debug OFF
            enable_debug_endpoints=False,
            enable_verbose_logging=False,
            enable_mock_responses=False,
        )
    
    @classmethod
    def for_development(cls) -> "FeatureFlags":
        """Get development feature flags (all enabled)."""
        return cls(
            # All features on
            enable_multimodal=True,
            enable_query_classifier=True,
            enable_compliance_check=True,
            enable_audit_trail=True,
            enable_context_cache=True,
            enable_semantic_cache=True,
            enable_agent_swarm=True,
            enable_curiosity_engine=True,
            # Safety still on
            enable_rate_limiting=True,
            enable_input_validation=True,
            enable_output_sanitization=True,
            # Debug on
            enable_debug_endpoints=True,
            enable_verbose_logging=True,
            enable_mock_responses=False,
        )
    
    @classmethod
    def for_staging(cls) -> "FeatureFlags":
        """Get staging feature flags (production + some experimental)."""
        flags = cls.for_production()
        flags.enable_semantic_cache = True
        flags.enable_verbose_logging = True
        return flags


@dataclass
class EnvironmentConfig:
    """
    Environment-specific configuration.
    
    Provides different settings for dev/staging/production.
    """
    
    mode: EnvironmentMode = EnvironmentMode.DEVELOPMENT
    features: FeatureFlags = field(default_factory=FeatureFlags)
    
    # Database
    database_url: str = ""
    redis_url: str = ""
    
    # Limits (conservative in production)
    max_concurrent_requests: int = 100
    max_request_size_mb: int = 10
    rate_limit_per_minute: int = 60
    
    # Timeouts (shorter in production for stability)
    request_timeout_seconds: int = 60
    research_timeout_seconds: int = 300
    tool_timeout_seconds: int = 30
    
    # Cache (larger in production)
    cache_size_mb: int = 100
    cache_ttl_seconds: int = 3600
    
    # Retry (more conservative in production)
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    
    # Logging
    log_level: str = "INFO"
    log_requests: bool = True
    log_responses: bool = False  # Too verbose
    
    @classmethod
    def for_production(cls) -> "EnvironmentConfig":
        """Production configuration - most stable."""
        return cls(
            mode=EnvironmentMode.PRODUCTION,
            features=FeatureFlags.for_production(),
            database_url=os.getenv("DATABASE_URL", ""),
            redis_url=os.getenv("REDIS_URL", ""),
            # Conservative limits
            max_concurrent_requests=50,
            max_request_size_mb=5,
            rate_limit_per_minute=30,
            # Short timeouts
            request_timeout_seconds=30,
            research_timeout_seconds=3600,  # 1 hour for deep research with many tools
            tool_timeout_seconds=20,
            # Large cache
            cache_size_mb=200,
            cache_ttl_seconds=7200,
            # Conservative retry
            max_retries=2,
            retry_delay_seconds=2.0,
            # Production logging
            log_level="WARNING",
            log_requests=True,
            log_responses=False,
        )
    
    @classmethod
    def for_development(cls) -> "EnvironmentConfig":
        """Development configuration - full features.
        
        NOTE: Requires DATABASE_URL environment variable (PostgreSQL).
        """
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logger.warning(
                "DATABASE_URL not set. PostgreSQL is required. "
                "Set DATABASE_URL=postgresql://user:pass@localhost:5432/project"
            )
        
        return cls(
            mode=EnvironmentMode.DEVELOPMENT,
            features=FeatureFlags.for_development(),
            database_url=database_url or "",  # Will fail gracefully if empty
            redis_url=os.getenv("REDIS_URL", ""),
            # Relaxed limits
            max_concurrent_requests=200,
            max_request_size_mb=50,
            rate_limit_per_minute=1000,
            # Long timeouts for debugging
            request_timeout_seconds=300,
            research_timeout_seconds=3600,  # 1 hour for deep research with many tools
            tool_timeout_seconds=120,
            # Small cache
            cache_size_mb=50,
            cache_ttl_seconds=300,
            # Aggressive retry for testing
            max_retries=5,
            retry_delay_seconds=0.5,
            # Verbose logging
            log_level="DEBUG",
            log_requests=True,
            log_responses=True,
        )
    
    @classmethod
    def for_staging(cls) -> "EnvironmentConfig":
        """Staging configuration - production-like with more logging."""
        config = cls.for_production()
        config.mode = EnvironmentMode.STAGING
        config.features = FeatureFlags.for_staging()
        config.log_level = "INFO"
        config.log_responses = True
        return config
    
    @classmethod
    def from_environment(cls) -> "EnvironmentConfig":
        """Create config from environment variables."""
        env = os.getenv("ENVIRONMENT", "development").lower()
        
        if env == "production":
            config = cls.for_production()
        elif env == "staging":
            config = cls.for_staging()
        else:
            config = cls.for_development()
        
        logger.info(f"Loaded {config.mode.value} environment config")
        return config
    
    @property
    def is_production(self) -> bool:
        return self.mode == EnvironmentMode.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        return self.mode == EnvironmentMode.DEVELOPMENT
    
    @property
    def is_staging(self) -> bool:
        return self.mode == EnvironmentMode.STAGING


# ============================================================================
# Singleton
# ============================================================================

_environment_config: EnvironmentConfig | None = None


def get_environment_config() -> EnvironmentConfig:
    """Get singleton environment config."""
    global _environment_config
    if _environment_config is None:
        _environment_config = EnvironmentConfig.from_environment()
    return _environment_config


def set_environment_config(config: EnvironmentConfig):
    """Override environment config (for testing)."""
    global _environment_config
    _environment_config = config


def is_feature_enabled(feature: str) -> bool:
    """Check if a feature is enabled."""
    config = get_environment_config()
    return getattr(config.features, f"enable_{feature}", False)
