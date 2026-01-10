"""
Prometheus Metrics.

Provides metrics for monitoring research engine performance.
"""

from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge, Info


# ============================================================================
# Tool Metrics
# ============================================================================

TOOL_INVOCATIONS = Counter(
    "research_tool_invocations_total",
    "Total number of tool invocations",
    ["tool_name", "server_name", "status"]
)

TOOL_DURATION = Histogram(
    "research_tool_duration_seconds",
    "Tool execution duration in seconds",
    ["tool_name", "server_name"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

ACTIVE_TOOLS = Gauge(
    "research_active_tools",
    "Number of currently executing tools",
    ["server_name"]
)


# ============================================================================
# LLM Metrics
# ============================================================================

LLM_REQUESTS = Counter(
    "research_llm_requests_total",
    "Total number of LLM requests",
    ["provider", "model", "status"]
)

LLM_TOKENS = Counter(
    "research_llm_tokens_total",
    "Total tokens used",
    ["provider", "model", "token_type"]  # token_type: prompt, completion, reasoning
)

LLM_DURATION = Histogram(
    "research_llm_duration_seconds",
    "LLM request duration in seconds",
    ["provider", "model"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0]
)


# ============================================================================
# Research Job Metrics
# ============================================================================

JOBS_TOTAL = Counter(
    "research_jobs_total",
    "Total number of research jobs",
    ["job_type", "status"]
)

JOBS_DURATION = Histogram(
    "research_jobs_duration_seconds",
    "Research job duration in seconds",
    ["job_type"],
    buckets=[10, 30, 60, 120, 300, 600, 1800, 3600]
)

ACTIVE_JOBS = Gauge(
    "research_active_jobs",
    "Number of currently running jobs",
    ["job_type"]
)

FACTS_EXTRACTED = Counter(
    "research_facts_extracted_total",
    "Total atomic facts extracted",
    ["domain"]
)


# ============================================================================
# API Metrics
# ============================================================================

API_REQUESTS = Counter(
    "research_api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status_code"]
)

API_DURATION = Histogram(
    "research_api_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)


# ============================================================================
# MCP Server Metrics
# ============================================================================

MCP_SERVERS_ACTIVE = Gauge(
    "research_mcp_servers_active",
    "Number of active MCP servers"
)

MCP_CONNECTIONS = Counter(
    "research_mcp_connections_total",
    "Total MCP server connections",
    ["server_name", "status"]
)


# ============================================================================
# System Info
# ============================================================================

SYSTEM_INFO = Info(
    "research_engine",
    "Research engine information"
)


def set_system_info(version: str, environment: str) -> None:
    """Set system info labels."""
    SYSTEM_INFO.info({
        "version": version,
        "environment": environment,
    })


# ============================================================================
# Helper Functions
# ============================================================================

def record_tool_call(
    tool_name: str,
    server_name: str,
    duration: float,
    success: bool
) -> None:
    """Record a tool invocation."""
    status = "success" if success else "error"
    TOOL_INVOCATIONS.labels(
        tool_name=tool_name,
        server_name=server_name,
        status=status
    ).inc()
    TOOL_DURATION.labels(
        tool_name=tool_name,
        server_name=server_name
    ).observe(duration)


def record_llm_request(
    provider: str,
    model: str,
    duration: float,
    prompt_tokens: int,
    completion_tokens: int,
    reasoning_tokens: int = 0,
    success: bool = True
) -> None:
    """Record an LLM request."""
    status = "success" if success else "error"
    LLM_REQUESTS.labels(provider=provider, model=model, status=status).inc()
    LLM_DURATION.labels(provider=provider, model=model).observe(duration)
    
    if prompt_tokens:
        LLM_TOKENS.labels(provider=provider, model=model, token_type="prompt").inc(prompt_tokens)
    if completion_tokens:
        LLM_TOKENS.labels(provider=provider, model=model, token_type="completion").inc(completion_tokens)
    if reasoning_tokens:
        LLM_TOKENS.labels(provider=provider, model=model, token_type="reasoning").inc(reasoning_tokens)


def record_api_request(
    method: str,
    endpoint: str,
    status_code: int,
    duration: float
) -> None:
    """Record an API request."""
    API_REQUESTS.labels(method=method, endpoint=endpoint, status_code=str(status_code)).inc()
    API_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
