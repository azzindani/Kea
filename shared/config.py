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

from pydantic import BaseModel, Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Application environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class AppSettings(BaseModel):
    """Core application metadata."""
    name: str = "Autonomous OS"
    version: str = "0.4.0"
    environment: Environment = Environment.DEVELOPMENT
    vocab_dir: str = "configs/vocab"
    knowledge_dir: str = "knowledge"
    default_tenant: str = "default"
    default_conversation_title: str = "New Conversation"


class ServiceSettings(BaseModel):
    """Registry of microservice locations."""
    gateway: str = "http://localhost:8000"
    orchestrator: str = "http://localhost:8001"
    mcp_host: str = "http://localhost:8002"
    rag_service: str = "http://localhost:8003"
    vault: str = "http://localhost:8004"
    swarm_manager: str = "http://localhost:8005"
    chronos: str = "http://localhost:8006"


class LLMModelInfo(BaseModel):
    """Deep metadata for an LLM model."""
    id: str
    name: str
    provider: str
    context_length: int
    supports_vision: bool = False
    supports_tools: bool = False
    pricing_input: float = 0.0  # per 1M tokens
    pricing_output: float = 0.0


class LLMProviderInfo(BaseModel):
    """Metadata for an LLM provider."""
    name: str
    enabled: bool = True
    base_url: str | None = None


class LLMSettings(BaseModel):
    """LLM configuration."""
    default_provider: str = "openrouter"
    default_model: str = Field(default="nvidia/nemotron-3-nano-30b-a3b:free")
    fallback_model: str = Field(default="stepfun/step-3.5-flash:free")
    temperature: float = 0.7
    max_tokens: int = 32768
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    enable_reasoning: bool = True
    openrouter_api_key: str = ""
    max_retries: int = 3
    retry_delay_base: float = 2.0
    retry_min_seconds: float = 1.0
    retry_max_seconds: float = 10.0
    token_limit_multiplier: float = 4.0  # Heuristic for token estimation
    
    # Provider Registry
    providers: list[LLMProviderInfo] = [
        LLMProviderInfo(
            name="openrouter", 
            enabled=True, 
            base_url="https://openrouter.ai/api/v1"
        )
    ]
    models: list[LLMModelInfo] = [
        LLMModelInfo(
            id="nvidia/nemotron-3-nano-30b-a3b:free",
            name="Nemotron 3 Nano",
            provider="openrouter",
            context_length=32768,
            supports_tools=True,
        ),
        LLMModelInfo(
            id="google/gemini-2.0-flash-exp:free",
            name="Gemini Flash 2.0",
            provider="openrouter",
            context_length=1000000,
            supports_vision=True,
            supports_tools=True,
            pricing_input=0.075,
            pricing_output=0.30,
        ),
        LLMModelInfo(
            id="anthropic/claude-3.5-sonnet",
            name="Claude 3.5 Sonnet",
            provider="openrouter",
            context_length=200000,
            supports_vision=True,
            supports_tools=True,
            pricing_input=3.0,
            pricing_output=15.0,
        ),
        LLMModelInfo(
            id="openai/gpt-4o",
            name="GPT-4o",
            provider="openrouter",
            context_length=128000,
            supports_vision=True,
            supports_tools=True,
            pricing_input=2.50,
            pricing_output=10.0,
        ),
    ]


class LoggingSettings(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    format: str = "console"
    service_name: str = "system-core"


class DatabaseSettings(BaseModel):
    """Database configuration."""
    url: str = "postgresql://localhost/system_db"
    min_connections: int = 5
    max_connections: int = 20
    connection_timeout: float = 30.0
    idle_timeout: float = 600.0
    max_retries: int = 3
    retry_delay: float = 2.0
    command_timeout: float = 60.0


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
    retry_backoff_factor: float = 0.5
    max_concurrent_tools: int = 5
    tool_timeout_seconds: float = 60.0
    connect_timeout: float = 120.0
    discovery_timeout: float = 10.0
    search_limit: int = 1000
    min_similarity: float = 0.0
    jit: JITSettings = JITSettings()
    
    # Protocol & Metadata
    protocol_version: str = "2024-11-05"
    client_name: str = "system-engine"
    client_version: str = "0.4.0"


class EmbeddingSettings(BaseModel):
    """Embedding configuration."""
    use_local: bool = True
    model_name: str = "Qwen/Qwen3-Embedding-0.6B"
    api_model: str = "qwen/qwen3-embedding-8b"
    dimension: int = 1024
    batch_size: int = 32
    max_length: int = 32768
    instruction: str = "Given a web search query, retrieve relevant passages that answer the query"
    api_url: str = "https://openrouter.ai/api/v1/embeddings"
    
    # Adaptive settings
    high_pressure_batch_size: int = 8
    med_pressure_batch_size: int = 16


class RerankerSettings(BaseModel):
    """Reranker configuration."""
    model_name: str = "Qwen/Qwen3-Reranker-0.6B"
    per_task_top_k: int = 32768
    final_batch_top_k: int = 32768
    max_length: int = 32768
    batch_size: int = 16
    instruction: str = "Given a web search query, retrieve relevant passages that answer the query"

    # Adaptive settings
    high_pressure_batch_size: int = 2
    med_pressure_batch_size: int = 4
    low_pressure_batch_size: int = 8


class VLSettings(BaseModel):
    """Vision-Language embedding configuration."""
    model_name: str = "Qwen/Qwen3-VL-Embedding-2B"
    dimension: int = 1024
    instruction: str = "Given a web search query, retrieve relevant passages that answer the query"


class VLRerankerSettings(BaseModel):
    """Vision-Language reranker configuration."""
    model_name: str = "Qwen/Qwen3-VL-Reranker-2B"
    instruction: str = "Given a web search query, retrieve relevant passages that answer the query"


class TimeoutSettings(BaseModel):
    """Standardized timeouts."""
    default: float = 30.0
    audit_log: float = 2.0
    llm_completion: float = 60.0
    llm_streaming: float = 120.0
    embedding_api: float = 60.0
    tool_execution: float = 300.0
    auth_token: float = 5.0
    short: float = 5.0
    long: float = 600.0


class HardwareSettings(BaseModel):
    """Hardware monitoring and resource settings."""
    ram_warning_percent: float = 75.0
    ram_critical_percent: float = 90.0
    cpu_warning_percent: float = 80.0
    check_interval_seconds: float = 5.0
    max_history: int = 100
    
    # Executor limits
    max_parallel_scrapers: int = 3
    max_parallel_llm_calls: int = 2
    max_parallel_db_writers: int = 2
    max_parallel_embedders: int = 1
    batch_size: int = 1000
    chunk_size_mb: int = 10
    scraper_timeout_seconds: int = 30
    llm_timeout_seconds: int = 60
    checkpoint_every_items: int = 100
    max_memory_percent: float = 80.0

    # Adative Heuristics
    worker_cap: int = 8
    ram_per_worker_gb: float = 2.0
    vram_min_embedding_gb: float = 2.0
    cpu_sample_interval: float = 0.1
    
    # Adaptive Divisors/Multipliers
    scraper_worker_multiplier: int = 2
    db_writer_worker_divisor: int = 2
    critical_pressure_divisor: int = 4
    high_pressure_divisor: int = 2
    moderate_pressure_multiplier: float = 0.75
    
    # Pressure Thresholds
    high_pressure_threshold: float = 0.80
    critical_pressure_threshold: float = 0.90
    moderate_pressure_threshold: float = 0.70

    # Environment Heuristics
    kaggle_scraper_limit: int = 10
    default_scraper_limit: int = 5
    colab_llm_limit: int = 2
    kaggle_llm_limit: int = 3
    max_llm_limit: int = 4
    high_ram_chunk_mb: int = 50
    med_ram_chunk_mb: int = 20
    low_ram_chunk_mb: int = 10
    constrained_scraper_timeout: int = 60
    constrained_llm_timeout: int = 120
    notebook_max_memory_percent: float = 75.0
    notebook_checkpoint_items: int = 50
    default_max_memory_percent: float = 85.0
    default_checkpoint_items: int = 100

    # Batch Size Heuristics
    batch_size_high_threshold: float = 16.0
    batch_size_med_threshold: float = 8.0
    batch_size_low_threshold: float = 4.0
    batch_size_high_val: int = 10000
    batch_size_med_val: int = 5000
    batch_size_low_val: int = 1000
    batch_size_min_val: int = 500

    # Search & Tool Discovery
    top_k_min: int = 20
    top_k_multiplier: int = 10
    search_limit_min: int = 10
    search_limit_max: int = 100
    search_limit_multiplier: float = 10.0
    constrained_ram_threshold: float = 8.0

    # Embedder Limits
    gpu_embedder_limit: int = 2
    cpu_embedder_limit: int = 1

    # RAM Thresholds
    high_ram_threshold_gb: float = 8.0
    med_ram_threshold_gb: float = 4.0
    
    # OOM Risk Limits
    vram_oom_limit_gb: float = 1.0
    ram_oom_limit_gb: float = 2.0


class KnowledgeSettings(BaseModel):
    """Knowledge retrieval settings for KnowledgeRetriever."""
    cache_ttl: float = 60.0
    min_similarity: float = 0.3
    default_limit: int = 3
    raw_search_limit: int = 5
    skill_limit: int = 3
    rule_limit: int = 2
    procedure_limit: int = 3
    timeout_search: float = 30.0
    timeout_raw: float = 10.0
    timeout_health: float = 3.0
    
    # Registry & Backend
    embedding_content_limit: int = 4000
    advisory_lock_id: int = 12346
    
    # Heuristics
    results_per_gb_ram: int = 10000
    max_results_cap: int = 100000
    tool_registry_multiplier: int = 300
    tool_registry_min: int = 100
    tool_registry_max: int = 10000
    fact_limit_sqrt_multiplier: int = 40
    fact_limit_min: int = 20
    fact_limit_max: int = 500
    
    # Scanner Defaults
    default_domain: str = "general"
    default_category: str = "skill"
    default_version: str = "1.0"
    frontmatter_delimiter: str = "---"
    excluded_filenames: list[str] = ["README.MD", "LIBRARY_MANIFEST.MD"]

    # Categories
    category_skill: str = "skill"
    category_rule: str = "rule"
    category_procedure: str = "procedure"
    category_persona: str = "persona"

    # Registry
    registry_table: str = "knowledge_registry"
    context_header: str = "DOMAIN EXPERTISE"


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
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    refresh_token_days: int = 7
    session_hours: int = 24
    allow_anonymous: bool = True
    api_key_header_name: str = "X-API-Key"
    password_min_length: int = 6
    api_key_default_rate_limit: int = 1000
    api_key_max_rate_limit: int = 10000
    api_key_prefix: str = "project_"
    default_scopes: list[str] = ["read", "write"]


class UserSettings(BaseModel):
    """User management settings."""
    default_list_limit: int = 100
    max_list_limit: int = 500
    default_role: str = "user"
    anonymous_user_id: str = "anonymous"
    anonymous_user_name: str = "Anonymous"


class ConversationSettings(BaseModel):
    """Conversation management settings."""
    default_limit: int = 50
    max_limit: int = 200
    search_limit: int = 20
    message_limit: int = 100
    message_max_limit: int = 500
    title_max_length: int = 50


class JobSettings(BaseModel):
    """Job management settings."""
    default_limit: int = 20
    max_limit: int = 100
    id_prefix: str = "job-"
    default_depth: int = 2
    default_max_steps: int = 20
    max_depth: int = 5
    max_steps: int = 100


class MemorySettings(BaseModel):
    """Memory (Insight/Graph) management settings."""
    search_limit: int = 10
    search_max_limit: int = 100
    min_confidence: float = 0.5
    graph_depth: int = 2
    graph_max_depth: int = 5
    graph_limit: int = 50
    session_limit: int = 100


class RateLimitSettings(BaseModel):
    """Global rate limiting settings."""
    enabled: bool = True
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10
    default_window_seconds: int = 60
    exempt_paths: list[str] = [
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/metrics",
    ]




class RAGSettings(BaseModel):
    """RAG Service settings."""
    default_min_score: float = 0.5
    default_limit: int = 20
    max_limit: int = 100
    ingest_max_rows: int = 1000
    batch_size: int = 50
    knowledge_limit: int = 5
    knowledge_candidate_multiplier: int = 5
    artifact_path: str = "./artifacts"
    default_confidence: float = 0.8
    min_confidence: float = 0.0


class VaultSettings(BaseModel):
    """Vault Service settings."""
    default_limit: int = 5
    max_limit: int = 100


class ChronosSettings(BaseModel):
    """Chronos scheduler settings."""
    poll_interval: float = 60.0
    due_tolerance: float = 30.0
    max_history_days: int = 30
    default_max_sources: int = 10


class SwarmSettings(BaseModel):
    """Swarm Manager (Governance) settings."""
    default_blacklist_duration_minutes: int = 30
    default_escalation_type: str = "error"
    poll_interval: float = 5.0
    max_agents_per_minute: int = 100
    max_tool_calls_per_minute: int = 100
    rate_limit_window_seconds: float = 60.0


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


class CircuitBreakerSettings(BaseModel):
    """Circuit breaker configuration."""
    failure_threshold: int = 5
    reset_timeout: float = 30.0


class S3Settings(BaseModel):
    """S3 Storage settings."""
    bucket: str = "system-artifacts"
    endpoint: str = "http://localhost:9000"
    access_key: str = ""
    secret_key: str = ""


class EnterpriseSettings(BaseModel):
    """Enterprise-scale limits (from constants.py)."""
    tool_limit: int = 100_000
    search_limit: int = 100_000
    fact_limit: int = 100_000
    batch_size: int = 10_000
    registry_limit: int = 100_000
    crawl_depth: int = 1_000
    max_tool_results: int = 1_000_000
    max_concurrent_tools: int = 1_000
    max_parallel_servers: int = 100


class SecuritySettings(BaseModel):
    """Security and CORS settings."""
    cors_origins: list[str] = ["*"]
    cors_methods: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_headers: list[str] = ["*"]
    hsts_max_age: int = 31536000
    hsts_include_subdomains: bool = True
    csp_policy: str = "default-src 'self'"
    max_body_size_mb: int = 10


class IdSettings(BaseModel):
    """ID generation and hashing settings."""
    # Entity type → strategy routing
    ulid_entities: list[str] = [
        "agent", "job", "memory", "signal", "task",
        "node", "workflow", "insight", "conversation",
    ]
    uuid_entities: list[str] = [
        "session", "nonce", "token", "request",
    ]
    # All other entity types with payload → deterministic hash

    # Stripe-style entity prefixes
    prefixes: dict[str, str] = {
        "agent": "agt_",
        "job": "job_",
        "signal": "sig_",
        "task": "tsk_",
        "node": "node_",
        "workflow": "wf_",
        "memory": "mem_",
        "session": "ses_",
        "nonce": "nonce_",
        "token": "tok_",
        "request": "req_",
        "document": "doc_",
        "embedding": "emb_",
        "insight": "ins_",
        "conversation": "conv_",
    }

    # Deterministic hash namespace (UUIDv5)
    hash_namespace: str = "kea.ai"


class CacheHierarchySettings(BaseModel):
    """Multi-tier cache hierarchy settings."""
    # L1: Working cache (current OODA cycle)
    l1_max_items: int = 9          # 7 ± 2

    # L2: Session cache (conversation scope)
    l2_max_items: int = 256
    l2_ttl_seconds: int = 300      # 5 min

    # L3: Result cache (cross-session deduplication)
    l3_max_items: int = 1024
    l3_ttl_seconds: int = 3600     # 60 min

    # L4: Decision cache (anti-oscillation ring buffer)
    l4_max_items: int = 64
    l4_ttl_seconds: int = 30

    # Pressure eviction batch size
    pressure_evict_batch_size: int = 32


class NormalizationSettings(BaseModel):
    """Mathematical normalization settings."""
    # Z-score clipping bound (values beyond ±N σ are clipped)
    z_score_clip: float = 3.0

    # Softmax temperature (higher = flatter distribution)
    softmax_temperature: float = 1.0

    # Source type → strategy routing
    bounded_sources: list[str] = [
        "cosine", "tool_confidence", "percentage", "similarity",
    ]
    unbounded_sources: list[str] = [
        "bm25", "tfidf", "relevance_score",
    ]
    distribution_sources: list[str] = [
        "classification", "intent", "category",
    ]


class KernelSettings(BaseModel):
    """Kernel Tier 1 through Tier 7 processing settings."""

    # --- T1: Classification ---
    classification_confidence_threshold: float = 0.80
    classification_linguistic_weight: float = 0.4
    classification_semantic_weight: float = 0.6
    classification_fallback_label: str = "UNCLASSIFIED"
    perception_automatic_threshold: float = 0.55  # Similarity needed to auto-detect domain

    # --- T1: Intent / Sentiment / Urgency ---
    intent_labels: list[str] = [
        "CREATE", "DELETE", "QUERY", "UPDATE", "NAVIGATE",
        "CONFIGURE", "ANALYZE", "COMMUNICATE", "UNKNOWN",
    ]
    sentiment_labels: list[str] = [
        "POSITIVE", "NEGATIVE", "NEUTRAL", "FRUSTRATED", "URGENT",
    ]
    urgency_bands: list[str] = [
        "CRITICAL", "HIGH", "NORMAL", "LOW",
    ]
    urgency_keywords_critical: list[str] = [
        "immediately", "asap", "emergency", "urgent", "critical",
        "now", "right now", "right away",
    ]
    urgency_keywords_high: list[str] = [
        "soon", "quickly", "fast", "priority", "important",
        "time-sensitive", "hurry",
    ]
    urgency_keywords_low: list[str] = [
        "whenever", "no rush", "low priority", "when you can",
        "at your convenience", "eventually", "someday",
    ]

    # --- T1: Scoring ---
    scoring_semantic_weight: float = 0.4
    scoring_precision_weight: float = 0.35
    scoring_reward_weight: float = 0.25
    scoring_admin_reward_boost: float = 0.15
    scoring_creative_semantic_boost: float = 0.10

    # --- T1: Validation ---
    validation_strict_mode: bool = True

    # --- T1: Modality ---
    modality_keyframe_interval_seconds: float = 5.0
    modality_supported_extensions: dict[str, str] = {
        ".txt": "TEXT", ".md": "TEXT", ".csv": "TEXT", ".json": "TEXT",
        ".pdf": "DOCUMENT", ".xlsx": "DOCUMENT", ".docx": "DOCUMENT",
        ".png": "IMAGE", ".jpg": "IMAGE", ".jpeg": "IMAGE",
        ".gif": "IMAGE", ".webp": "IMAGE", ".svg": "IMAGE",
        ".mp3": "AUDIO", ".wav": "AUDIO", ".flac": "AUDIO", ".ogg": "AUDIO",
        ".mp4": "VIDEO", ".avi": "VIDEO", ".mov": "VIDEO", ".mkv": "VIDEO",
    }

    # --- T1: Location & Time ---
    temporal_recency_mappings: dict[str, int] = {
        "email": 86400,        # 24 hours in seconds
        "chat": 3600,          # 1 hour
        "stock": 300,          # 5 minutes
        "news": 259200,        # 3 days
        "log": 86400,          # 24 hours
        "default": 604800,     # 7 days
    }
    spatial_scope_multipliers: dict[str, float] = {
        "coffee": 0.005,       # ~500m radius in degrees
        "restaurant": 0.01,    # ~1km
        "logistics": 1.0,      # ~100km
        "travel": 10.0,        # ~1000km
        "default": 0.1,        # ~10km
    }

    # --- T2: What-If / Simulation ---
    risk_threshold_approve: float = 0.3
    risk_threshold_reject: float = 0.7
    max_simulation_branches: int = 8

    # --- T2: Attention / Plausibility ---
    attention_relevance_threshold: float = 0.3
    plausibility_confidence_threshold: float = 0.6

    # --- T2: Curiosity ---
    curiosity_strategy_mappings: dict[str, str] = {
        "knowledge": "RAG",
        "factual": "WEB",
        "tool": "SCAN",
        "context": "RAG",
        "default": "RAG",
    }

    # --- T2: Task Decomposition ---
    complexity_atomic_threshold: int = 1
    complexity_compound_threshold: int = 3

    # --- T3: Graph Synthesizer ---
    max_dag_review_iterations: int = 3
    max_parallel_branches: int = 16
    dag_compilation_timeout_ms: float = 5000.0

    # --- T3: Node Assembler ---
    node_execution_timeout_ms: float = 30000.0
    node_input_validation_strict: bool = True
    node_output_validation_strict: bool = True

    # --- T3: Advanced Planning ---
    planning_speed_weight: float = 0.4
    planning_cost_weight: float = 0.3
    planning_fidelity_weight: float = 0.3
    max_hypothesis_count: int = 10

    # --- T3: Reflection & Guardrails ---
    guardrail_max_consensus_candidates: int = 5
    guardrail_approval_threshold: float = 0.7
    guardrail_forbidden_actions: list[str] = [
        "data_exfiltration", "unauthorized_access", "privilege_escalation",
        "privacy_violation", "resource_abuse",
    ]
    reflection_min_score_gap: float = 0.2

    # --- T4: OODA Loop ---
    ooda_max_cycles: int = 10
    ooda_poll_timeout_ms: float = 1000.0
    ooda_tick_interval_ms: float = 50.0
    ooda_blocked_retry_limit: int = 3

    # --- T4: Async Multitasking ---
    async_poll_interval_ms: float = 2000.0
    max_parked_dags: int = 32
    context_switch_overhead_ms: float = 10.0

    # --- T4: Short-Term Memory ---
    stm_max_events: int = 256
    stm_max_entities: int = 512
    stm_default_entity_ttl_seconds: int = 3600
    stm_max_age_seconds: int = 7200
    stm_context_max_items: int = 50

    # --- T5: Lifecycle Controller ---
    lifecycle_panic_retry_interval_ms: float = 600000.0  # 10 minutes
    lifecycle_epoch_commit_threshold: int = 5  # objectives completed before commit
    lifecycle_max_objectives: int = 100

    # --- T5: Energy & Interrupts ---
    budget_token_limit: int = 1_000_000
    budget_cost_limit: float = 100.0
    budget_epoch_token_limit: int = 200_000
    budget_warning_threshold: float = 0.8  # warn at 80% consumption
    budget_exhaustion_threshold: float = 0.95

    # --- T6: Self Model ---
    self_model_calibration_window: int = 100
    self_model_calibration_ema_decay: float = 0.1
    self_model_capability_cache_ttl_seconds: int = 300

    # --- T6: Activation Router ---
    activation_urgency_weight: float = 0.30
    activation_structural_weight: float = 0.25
    activation_domain_weight: float = 0.25
    activation_gap_weight: float = 0.20
    activation_cache_ttl_seconds: int = 30
    activation_pressure_moderate: float = 0.6
    activation_pressure_high: float = 0.8
    activation_embedding_threshold: float = 0.75 # Similarity needed for fast-path return

    # --- T6: Cognitive Load Monitor ---
    load_compute_weight: float = 0.40
    load_time_weight: float = 0.35
    load_breadth_weight: float = 0.25
    load_loop_detection_window: int = 10
    load_loop_repeat_threshold: int = 3
    load_stall_multiplier: float = 3.0
    load_threshold_simplify: float = 0.6
    load_threshold_escalate: float = 0.8
    load_threshold_abort: float = 0.95
    load_goal_drift_threshold: float = 0.4

    # --- T6: Hallucination Monitor ---
    grounding_similarity_threshold: float = 0.65
    grounding_inferred_weight: float = 0.5
    grounding_grounded_weight: float = 1.0
    grounding_fabricated_weight: float = 0.0

    # --- T6: Confidence Calibrator ---
    calibration_overconfidence_threshold: float = 0.2
    calibration_underconfidence_threshold: float = 0.2
    calibration_default_curve: dict[str, float] = {
        "0.0": 0.0, "0.1": 0.1, "0.2": 0.2, "0.3": 0.3,
        "0.4": 0.4, "0.5": 0.5, "0.6": 0.6, "0.7": 0.7,
        "0.8": 0.8, "0.9": 0.9, "1.0": 1.0,
    }

    # --- T6: Noise Gate ---
    noise_gate_grounding_threshold: float = 0.6
    noise_gate_confidence_threshold: float = 0.5
    noise_gate_max_retries: int = 3

    # --- T7: Conscious Observer (Human Kernel Apex) ---
    conscious_observer_emergency_max_cycles: int = 3
    conscious_observer_expected_cycle_ms: float = 2000.0
    conscious_observer_simplify_max_steps: int = 2


class HttpStatusSettings(BaseModel):
    """Standardized HTTP Status Codes."""
    ok: int = 200
    created: int = 201
    accepted: int = 202
    no_content: int = 204
    bad_request: int = 400
    unauthorized: int = 401
    forbidden: int = 403
    not_found: int = 404
    method_not_allowed: int = 405
    conflict: int = 409
    payload_too_large: int = 413
    unprocessable_entity: int = 422
    too_many_requests: int = 429
    internal_error: int = 500
    not_implemented: int = 501
    bad_gateway: int = 502
    service_unavailable: int = 503


class Settings(BaseSettings):
    """
    Main settings class.
    Loads from environment variables and .env files.
    """
    # Root Aliases (Mapping environment variables directly to root fields or nested models)
    openrouter_api_key: str = Field(default="", validation_alias=AliasChoices("OPENROUTER_API_KEY", "LLM_OPENROUTER_API_KEY"))
    database_url: str = Field(default="", validation_alias=AliasChoices("DATABASE_URL", "DATABASE_URL"))
    jwt_secret: str = Field(default="", validation_alias=AliasChoices("JWT_SECRET", "AUTH_JWT_SECRET"))
    redis_url: str = Field(default="", validation_alias=AliasChoices("REDIS_URL"))
    
    # Nested configs
    app: AppSettings = AppSettings()
    services: ServiceSettings = ServiceSettings()
    llm: LLMSettings = LLMSettings()
    logging: LoggingSettings = LoggingSettings()
    database: DatabaseSettings = DatabaseSettings()
    mcp: MCPSettings = MCPSettings()
    embedding: EmbeddingSettings = EmbeddingSettings()
    reranker: RerankerSettings = RerankerSettings()
    vl_embedding: VLSettings = VLSettings()
    vl_reranker: VLRerankerSettings = VLRerankerSettings()
    timeouts: TimeoutSettings = TimeoutSettings()
    governance: GovernanceSettings = GovernanceSettings()
    auth: AuthSettings = AuthSettings()
    api: ApiSettings = ApiSettings()
    feature_flags: FeatureFlags = FeatureFlags()
    s3: S3Settings = S3Settings()
    security: SecuritySettings = SecuritySettings()
    chronos: ChronosSettings = ChronosSettings()
    circuit_breaker: CircuitBreakerSettings = CircuitBreakerSettings()
    rate_limit: RateLimitSettings = RateLimitSettings()
    rag: RAGSettings = RAGSettings()
    vault_settings: VaultSettings = VaultSettings()
    conversations: ConversationSettings = ConversationSettings()
    jobs: JobSettings = JobSettings()
    memory: MemorySettings = MemorySettings()
    users: UserSettings = UserSettings()
    swarm: SwarmSettings = SwarmSettings()
    enterprise: EnterpriseSettings = EnterpriseSettings()
    hardware: HardwareSettings = HardwareSettings()
    knowledge: KnowledgeSettings = KnowledgeSettings()
    status_codes: HttpStatusSettings = HttpStatusSettings()
    ids: IdSettings = IdSettings()
    cache_hierarchy: CacheHierarchySettings = CacheHierarchySettings()
    normalization: NormalizationSettings = NormalizationSettings()
    kernel: KernelSettings = KernelSettings()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__"
    )

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        # Post-load sync
        if self.openrouter_api_key:
            self.llm.openrouter_api_key = self.openrouter_api_key
        if self.database_url:
            self.database.url = self.database_url
        if self.jwt_secret:
            self.auth.jwt_secret = self.jwt_secret

    @property
    def is_development(self) -> bool:
        return self.app.environment == Environment.DEVELOPMENT


@lru_cache()
def get_settings() -> Settings:
    return Settings()
