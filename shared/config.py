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
import re

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """Application environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class AppSettings(BaseModel):
    """Core application metadata."""
    name: str = "Project Research Engine"
    version: str = "0.4.0"
    environment: str = "development"


class ServiceSettings(BaseModel):
    """Registry of microservice locations."""
    gateway: str | None = None
    orchestrator: str | None = None
    mcp_host: str | None = None
    rag_service: str | None = None
    vault: str | None = None
    swarm_manager: str | None = None
    chronos: str | None = None


class LLMSettings(BaseModel):
    """LLM configuration."""
    default_provider: str = "openrouter"
    default_model: str = "nvidia/nemotron-3-nano-30b-a3b:free"
    fallback_model: str = "stepfun/step-3.5-flash:free"
    temperature: float = 0.7
    max_tokens: int = 32768
    enable_reasoning: bool = True
    openrouter_api_key: str = ""


class LoggingSettings(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "json"
    service_name: str = "research-engine"


class DatabaseSettings(BaseModel):
    """Database configuration."""
    url: str = ""
    min_connections: int = 5
    max_connections: int = 20
    connection_timeout: float = 30.0
    idle_timeout: float = 600.0


class JITSettings(BaseModel):
    """Just-In-Time Server Spawning Configuration."""
    enabled: bool = True
    uv_enabled: bool = True
    uv_path: str | None = None
    idle_timeout: float = 300.0
    max_servers: int = 20
    connect_timeout: float = 120.0
    allowed_dirs: list[str] = Field(default_factory=list)


class MCPSettings(BaseModel):
    """MCP configuration."""
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    max_concurrent_tools: int = 5
    tool_timeout_seconds: float = 60.0
    jit: JITSettings = JITSettings()


class EmbeddingSettings(BaseModel):
    """Embedding configuration."""
    use_local: bool = True
    model_name: str = "Qwen/Qwen3-Embedding-0.6B"
    api_model: str = "qwen/qwen3-embedding-8b"
    dimension: int = 1024
    batch_size: int = 32


class RerankerSettings(BaseModel):
    """Reranker configuration."""
    model_name: str = "Qwen/Qwen3-Reranker-0.6B"
    per_task_top_k: int = 32768
    final_batch_top_k: int = 32768
    max_length: int = 32768


class TimeoutSettings(BaseModel):
    """Standardized timeouts."""
    default: float = 30.0
    audit_log: float = 2.0
    llm_completion: float = 60.0
    llm_streaming: float = 120.0
    tool_execution: float = 300.0
    auth_token: float = 5.0
    short: float = 5.0
    long: float = 600.0


class GovernanceSettings(BaseModel):
    """Resource governance settings."""
    max_concurrent_cost: int = 100
    max_ram_percent: float = 85.0
    max_cpu_percent: float = 90.0
    max_agents: int = 50
    poll_interval: float = 1.0


class AuthSettings(BaseModel):
    """Auth & Session configuration."""
    jwt_secret: str = ""
    access_token_minutes: int = 60
    refresh_token_days: int = 7
    session_hours: int = 24


class ResearchSettings(BaseModel):
    """Research default parameters."""
    default_depth: int = 2
    default_max_sources: int = 10
    max_depth: int = 5
    max_sources: int = 50


class ApiSettings(BaseModel):
    """API infrastructure settings."""
    host: str = "0.0.0.0"
    workers_dev: int = 1
    workers_prod: int = 4
    default_limit: int = 100
    max_connections: int = 20


class FeatureFlags(BaseModel):
    """Feature flags."""
    enable_multimodal: bool = True
    enable_audit_trail: bool = True
    enable_context_cache: bool = True
    enable_semantic_cache: bool = False
    enable_rate_limiting: bool = True
    enable_input_validation: bool = True
    enable_output_sanitization: bool = True
    enable_debug_endpoints: bool = False
    enable_verbose_logging: bool = False
    enable_mock_responses: bool = False


class S3Settings(BaseModel):
    """S3 Storage settings."""
    bucket: str = "research-artifacts"
    endpoint: str = ""
    access_key: str = ""
    secret_key: str = ""


class SecuritySettings(BaseModel):
    """Security and CORS settings."""
    cors_origins: list[str] = ["*"]


class Settings(BaseSettings):
    """
    Main settings class.
    Loads from environment variables and settings.yaml.
    """
    # Legacy/Root Aliases (for backward compatibility and easy Env mapping)
    openrouter_api_key: str = ""
    database_url: str = ""
    redis_url: str = ""
    
    # Nested configs
    app: AppSettings = AppSettings()
    services: ServiceSettings = ServiceSettings()
    llm: LLMSettings = LLMSettings()
    logging: LoggingSettings = LoggingSettings()
    database: DatabaseSettings = DatabaseSettings()
    mcp: MCPSettings = MCPSettings()
    embedding: EmbeddingSettings = EmbeddingSettings()
    reranker: RerankerSettings = RerankerSettings()
    timeouts: TimeoutSettings = TimeoutSettings()
    governance: GovernanceSettings = GovernanceSettings()
    auth: AuthSettings = AuthSettings()
    research: ResearchSettings = ResearchSettings()
    api: ApiSettings = ApiSettings()
    feature_flags: FeatureFlags = FeatureFlags()
    s3: S3Settings = S3Settings()
    security: SecuritySettings = SecuritySettings()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        env_nested_delimiter = "__" # Double underscore for nesting

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._load_yaml_config()
        self._sync_aliases()

    def _sync_aliases(self):
        """Sync root aliases to nested models if provided."""
        if self.openrouter_api_key:
            self.llm.openrouter_api_key = self.openrouter_api_key
        if self.database_url:
            self.database.url = self.database_url
        if self.app.environment:
            # Simple conversion to str if needed
            pass

    def _update_nested_config(self, field_name: str, yaml_data: dict[str, Any], model_class: type[BaseModel]) -> None:
        """Merge YAML config with existing Env-loaded config."""
        if field_name not in yaml_data:
            return

        current_val = getattr(self, field_name)
        # Combine existing (from Env) with YAML
        env_overrides = current_val.model_dump(exclude_unset=True)
        new_data = yaml_data[field_name].copy()
        new_data.update(env_overrides)
        setattr(self, field_name, model_class(**new_data))

    def _load_yaml_config(self) -> None:
        """Load configuration from configs/settings.yaml."""
        config_path = Path("configs/settings.yaml")
        if not config_path.exists():
            return

        try:
            with open(config_path) as f:
                yaml_content = f.read()
            
            # Env var substitution: ${VAR_NAME:default}
            pattern = re.compile(r'\$\{([^}:]+)(?::([^}]*))?\}')
            yaml_with_env = pattern.sub(
                lambda m: os.getenv(m.group(1), m.group(2) or ""), 
                yaml_content
            )
            yaml_config = yaml.safe_load(yaml_with_env)

            if not yaml_config:
                return

            # Apply all nested updates
            models_to_update = {
                "app": AppSettings,
                "services": ServiceSettings,
                "llm": LLMSettings,
                "logging": LoggingSettings,
                "database": DatabaseSettings,
                "mcp": MCPSettings,
                "embedding": EmbeddingSettings,
                "reranker": RerankerSettings,
                "timeouts": TimeoutSettings,
                "governance": GovernanceSettings,
                "auth": AuthSettings,
                "research": ResearchSettings,
                "api": ApiSettings,
                "feature_flags": FeatureFlags,
                "s3": S3Settings,
                "security": SecuritySettings,
            }
            
            for field_name, model_cls in models_to_update.items():
                self._update_nested_config(field_name, yaml_config, model_cls)

        except Exception:
            pass

@lru_cache()
def get_settings() -> Settings:
    return Settings()
