"""
Business Metrics.

Prometheus metrics for monitoring business KPIs.
"""

from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge, Info

from shared.logging import get_logger


logger = get_logger(__name__)


# ============================================================================
# System Metrics
# ============================================================================

SYSTEM_INFO = Info(
    "project_system",
    "System information",
)

ACTIVE_USERS = Gauge(
    "project_active_users",
    "Number of active users (sessions in last 24h)",
)

ACTIVE_CONVERSATIONS = Gauge(
    "project_active_conversations",
    "Number of active conversations (messages in last 24h)",
)


# ============================================================================
# Authentication Metrics
# ============================================================================

AUTH_ATTEMPTS = Counter(
    "project_auth_attempts_total",
    "Total authentication attempts",
    ["method", "status"],
)

AUTH_LATENCY = Histogram(
    "project_auth_latency_seconds",
    "Authentication latency",
    ["method"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

ACTIVE_SESSIONS = Gauge(
    "project_active_sessions",
    "Number of active sessions",
)


# ============================================================================
# Conversation Metrics
# ============================================================================

CONVERSATIONS_CREATED = Counter(
    "project_conversations_created_total",
    "Total conversations created",
)

MESSAGES_SENT = Counter(
    "project_messages_sent_total",
    "Total messages sent",
    ["role"],  # user, assistant
)

MESSAGE_LENGTH = Histogram(
    "project_message_length_chars",
    "Message length in characters",
    ["role"],
    buckets=[10, 50, 100, 250, 500, 1000, 2500, 5000],
)


# ============================================================================
# Research Metrics
# ============================================================================

RESEARCH_REQUESTS = Counter(
    "project_research_requests_total",
    "Total research requests",
    ["query_type", "status"],
)

RESEARCH_DURATION = Histogram(
    "project_research_duration_seconds",
    "Research duration",
    ["query_type"],
    buckets=[1, 5, 10, 30, 60, 120, 300],
)

RESEARCH_CONFIDENCE = Histogram(
    "project_research_confidence",
    "Research confidence score",
    buckets=[0.1, 0.25, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0],
)

SOURCES_PER_RESEARCH = Histogram(
    "project_sources_per_research",
    "Number of sources per research",
    buckets=[1, 2, 5, 10, 15, 20, 30],
)

CACHE_HITS = Counter(
    "project_cache_hits_total",
    "Total cache hits",
    ["cache_type"],  # research, context
)

CACHE_MISSES = Counter(
    "project_cache_misses_total",
    "Total cache misses",
    ["cache_type"],
)


# ============================================================================
# Tool Metrics
# ============================================================================

TOOL_CALLS = Counter(
    "project_tool_calls_total",
    "Total MCP tool calls",
    ["tool_name", "status"],
)

TOOL_DURATION = Histogram(
    "project_tool_duration_seconds",
    "Tool execution duration",
    ["tool_name"],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30],
)


# ============================================================================
# Rate Limiting Metrics
# ============================================================================

RATE_LIMIT_HITS = Counter(
    "project_rate_limit_hits_total",
    "Total rate limit hits",
    ["limit_type"],  # user, ip
)


# ============================================================================
# Error Metrics
# ============================================================================

ERRORS = Counter(
    "project_errors_total",
    "Total errors",
    ["error_type", "endpoint"],
)


# ============================================================================
# Helper Functions
# ============================================================================

def record_auth_attempt(method: str, success: bool, duration: float):
    """Record authentication attempt."""
    status = "success" if success else "failure"
    AUTH_ATTEMPTS.labels(method=method, status=status).inc()
    AUTH_LATENCY.labels(method=method).observe(duration)


def record_message(role: str, content: str):
    """Record message sent."""
    MESSAGES_SENT.labels(role=role).inc()
    MESSAGE_LENGTH.labels(role=role).observe(len(content))


def record_research(
    query_type: str,
    success: bool,
    duration: float,
    confidence: float = 0.0,
    sources_count: int = 0,
    was_cached: bool = False,
):
    """Record research request."""
    status = "success" if success else "failure"
    RESEARCH_REQUESTS.labels(query_type=query_type, status=status).inc()
    RESEARCH_DURATION.labels(query_type=query_type).observe(duration)
    
    if success:
        RESEARCH_CONFIDENCE.observe(confidence)
        SOURCES_PER_RESEARCH.observe(sources_count)
    
    if was_cached:
        CACHE_HITS.labels(cache_type="research").inc()
    else:
        CACHE_MISSES.labels(cache_type="research").inc()


def record_tool_call(tool_name: str, success: bool, duration: float):
    """Record tool call."""
    status = "success" if success else "failure"
    TOOL_CALLS.labels(tool_name=tool_name, status=status).inc()
    TOOL_DURATION.labels(tool_name=tool_name).observe(duration)


def record_error(error_type: str, endpoint: str):
    """Record error."""
    ERRORS.labels(error_type=error_type, endpoint=endpoint).inc()
