"""
Environment Configuration System.

Provides unified configuration loading from environment and YAML files.
"""

from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """Application environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class LLMSettings(BaseModel):
    """LLM configuration."""

    default_provider: str = "openrouter"
    default_model: str = "nvidia/nemotron-3-nano-30b-a3b:free"
    temperature: float = 0.7
    max_tokens: int = 32768
    enable_reasoning: bool = True


class LoggingSettings(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    format: str = "json"
    service_name: str = "research-engine"


class MCPServerConfig(BaseModel):
    """MCP server configuration."""

    name: str
    enabled: bool = True
    transport: str = "stdio"
    command: str | None = None
    url: str | None = None


class MCPSettings(BaseModel):
    """MCP configuration with retry settings."""

    servers: list[MCPServerConfig] = Field(default_factory=list)

    # Retry configuration
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    retry_on_timeout: bool = True
    retry_on_connection_error: bool = True

    max_concurrent_tools: int = 5
    tool_timeout_seconds: float = 60.0

    # JIT Configuration
    jit: JITSettings = Field(default_factory=lambda: JITSettings())


class JITSettings(BaseModel):
    """Just-In-Time Server Spawning Configuration."""

    enabled: bool = True
    uv_enabled: bool = True
    uv_path: str | None = None
    idle_timeout: float = 300.0  # 5 minutes
    max_servers: int = 20
    allowed_dirs: list[str] = Field(default_factory=list)  # Security whitelist (optional)


class ResearchSettings(BaseModel):
    """Research configuration."""

    max_depth: int = 3
    max_sources: int = 10
    timeout_seconds: int = 300
    parallel_tools: int = 5


class EmbeddingSettings(BaseModel):
    """Embedding configuration."""

    use_local: bool = True  # Use local GPU if available, else API
    model_name: str = "Qwen/Qwen3-Embedding-0.6B"
    api_model: str = "qwen/qwen3-embedding-8b"  # OpenRouter model
    dimension: int = 1024
    batch_size: int = 32


class RerankerSettings(BaseModel):
    """Reranker configuration."""

    model_name: str = "Qwen/Qwen3-Reranker-0.6B"
    per_task_top_k: int = 32768  # Top-k after each tool
    final_batch_top_k: int = 32768  # Top-k before generation
    max_length: int = 32768


class ConfidenceSettings(BaseModel):
    """Adaptive confidence loop configuration."""

    initial_threshold: float = 0.95
    degradation_rate: float = 0.05
    min_threshold: float = 0.60
    max_loops: int = 32768


class LoopSafetySettings(BaseModel):
    """Loop safety controls."""

    max_global_iterations: int = 32768
    max_facts_threshold: int = 32768


class TimeoutSettings(BaseModel):
    """Standardized timeouts for the entire system."""

    default: float = 30.0
    audit_log: float = 2.0
    llm_completion: float = 60.0
    llm_streaming: float = 120.0
    tool_execution: float = 300.0
    short: float = 5.0
    long: float = 600.0


class ModelDefaults(BaseModel):
    """Centralized model defaults."""

    default_model: str = "nvidia/nemotron-3-nano-30b-a3b:free"
    app_name: str = "research-engine"
    planner_model: str = "nvidia/nemotron-3-nano-30b-a3b:free"
    critic_model: str = "nvidia/nemotron-3-nano-30b-a3b:free"
    generator_model: str = "nvidia/nemotron-3-nano-30b-a3b:free"


class GovernanceSettings(BaseModel):
    """Resource governance settings."""

    max_concurrent_cost: int = 100
    max_ram_percent: float = 85.0
    max_cpu_percent: float = 90.0
    poll_interval: float = 1.0


class Settings(BaseSettings):
    """
    Main settings class.

    Loads from environment variables and settings.yaml.
    """

    # Environment
    environment: Environment = Environment.DEVELOPMENT

    # API Keys
    openrouter_api_key: str = ""
    openrouter_model: str = "nvidia/nemotron-3-nano-30b-a3b:free"

    # Database
    database_url: str = "postgresql://localhost/research_engine"
    redis_url: str = "redis://localhost:6379"

    # Storage
    s3_bucket: str = "research-artifacts"
    s3_endpoint: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    jwt_secret: str = ""

    # Logging
    log_level: str = "INFO"
    log_format: str = "console"

    # Search APIs
    tavily_api_key: str = ""
    brave_api_key: str = ""

    # Nested configs (loaded from YAML)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    mcp: MCPSettings = Field(default_factory=MCPSettings)
    research: ResearchSettings = Field(default_factory=ResearchSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    reranker: RerankerSettings = Field(default_factory=RerankerSettings)
    confidence: ConfidenceSettings = Field(default_factory=ConfidenceSettings)
    loop_safety: LoopSafetySettings = Field(default_factory=LoopSafetySettings)

    # New Configs (Deep Audit Fixes)
    timeouts: TimeoutSettings = Field(default_factory=TimeoutSettings)
    models: ModelDefaults = Field(default_factory=ModelDefaults)
    governance: GovernanceSettings = Field(default_factory=GovernanceSettings)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        env_nested_delimiter = "_"

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._load_yaml_config()

    def _update_nested_config(self, field_name: str, yaml_data: dict[str, Any], model_class: type[BaseModel]) -> None:
        """
        Merge YAML config with existing Env-loaded config.
        Priority: Env > YAML > Defaults
        """
        if field_name not in yaml_data:
            return

        current_val = getattr(self, field_name)
        if isinstance(current_val, BaseModel):
            # Get values explicitly set by Env/Init (not defaults)
            # Note: This relies on pydantic tracking 'set' fields.
            env_overrides = current_val.model_dump(exclude_unset=True)
            
            # Start with YAML (overrides defaults)
            new_data = yaml_data[field_name].copy()
            
            # Apply Env overrides (overrides YAML)
            new_data.update(env_overrides)
            
            # Re-instantiate
            setattr(self, field_name, model_class(**new_data))

    def _load_yaml_config(self) -> None:
        """Load additional configuration from settings.yaml."""
        config_path = Path("configs/settings.yaml")
        if not config_path.exists():
            return

        try:
            with open(config_path) as f:
                yaml_config = yaml.safe_load(f)

            if not yaml_config:
                return

            # Update nested configs with merge logic
            self._update_nested_config("llm", yaml_config, LLMSettings)
            self._update_nested_config("logging", yaml_config, LoggingSettings)
            self._update_nested_config("mcp", yaml_config, MCPSettings)
            self._update_nested_config("research", yaml_config, ResearchSettings)
            self._update_nested_config("embedding", yaml_config, EmbeddingSettings)
            self._update_nested_config("reranker", yaml_config, RerankerSettings)
            self._update_nested_config("confidence", yaml_config, ConfidenceSettings)
            self._update_nested_config("loop_safety", yaml_config, LoopSafetySettings)
            self._update_nested_config("timeouts", yaml_config, TimeoutSettings)
            self._update_nested_config("models", yaml_config, ModelDefaults)
            self._update_nested_config("governance", yaml_config, GovernanceSettings)

        except Exception:
            # Silently fail if YAML loading fails
            pass

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == Environment.PRODUCTION


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings instance
    """
    return Settings()
