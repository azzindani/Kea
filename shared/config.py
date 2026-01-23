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
    max_tokens: int = 4096
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
    
    # Rate limiting
    rate_limit_per_second: float = 10.0
    max_concurrent_tools: int = 5
    tool_timeout_seconds: float = 60.0


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
    per_task_top_k: int = 10  # Top-k after each tool
    final_batch_top_k: int = 50  # Top-k before generation
    max_length: int = 8192


class ConfidenceSettings(BaseModel):
    """Adaptive confidence loop configuration."""
    initial_threshold: float = 0.95
    degradation_rate: float = 0.05
    min_threshold: float = 0.60
    max_loops: int = 5


class LoopSafetySettings(BaseModel):
    """Loop safety controls."""
    max_global_iterations: int = 10
    max_facts_threshold: int = 1000


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
    
    # Vector DB
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    
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
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._load_yaml_config()
    
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
            
            # Load nested configs
            if "llm" in yaml_config:
                self.llm = LLMSettings(**yaml_config["llm"])
            if "logging" in yaml_config:
                self.logging = LoggingSettings(**yaml_config["logging"])
            if "mcp" in yaml_config:
                self.mcp = MCPSettings(**yaml_config["mcp"])
            if "research" in yaml_config:
                self.research = ResearchSettings(**yaml_config["research"])
                
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
