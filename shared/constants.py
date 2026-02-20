"""
Enterprise-scale constants for Project v0.4.0.

Central constants file defining limits that replace hardcoded values across the codebase.
These are designed for 100K+ tool handling and enterprise-scale operations.
"""

from __future__ import annotations


# ============================================================================
# Tool Limits (Enterprise Scale: 100K+)
# ============================================================================

# Default limits (can be overridden by hardware detection)
DEFAULT_TOOL_LIMIT = 100_000           # Tool search results
DEFAULT_SEARCH_LIMIT = 100_000         # Web/API search
DEFAULT_FACT_LIMIT = 100_000           # Semantic fact search
DEFAULT_BATCH_SIZE = 10_000            # Batch processing
DEFAULT_REGISTRY_LIMIT = 100_000       # Tool registry queries
DEFAULT_CRAWL_DEPTH = 100_000          # Crawler depth limit

# Minimum limits (for constrained environments)
MIN_TOOL_LIMIT = 100
MIN_SEARCH_LIMIT = 10
MIN_FACT_LIMIT = 20
MIN_BATCH_SIZE = 10

# Maximum limits (safety caps)
MAX_TOOL_LIMIT = 1_000_000
MAX_CONCURRENT_TOOLS = 1_000
MAX_PARALLEL_SERVERS = 100
MAX_RESULTS_CAP = 1_000_000


# ============================================================================
# MCP Server Limits
# ============================================================================

# Search limits
SEARCH_MAX_RESULTS = 100_000
DDG_MAX_RESULTS = 100_000
GOOGLE_MAX_RESULTS = 100_000
ACADEMIC_MAX_RESULTS = 100_000
NEWS_MAX_RESULTS = 100_000

# Crawler limits
CRAWLER_MAX_PAGES = 100_000
CRAWLER_MAX_DEPTH = 1_000
SITEMAP_MAX_URLS = 100_000

# Financial data limits
STOCK_HISTORY_LIMIT = 100_000
OHLCV_LIMIT = 100_000
ORDER_BOOK_LIMIT = 100_000
TRADES_LIMIT = 100_000

# Document limits
PDF_MAX_PAGES = 100_000
EXCEL_MAX_ROWS = 1_000_000
CSV_MAX_ROWS = 1_000_000

# Analysis limits
FUZZY_MATCH_LIMIT = 100_000
ENTITY_EXTRACT_LIMIT = 100_000


# ============================================================================
# Service Limits
# ============================================================================

# Vault/Audit
AUDIT_QUERY_LIMIT = 100_000
FACT_STORE_LIMIT = 100_000

# RAG Service
RAG_SEARCH_LIMIT = 100_000
EMBEDDING_BATCH_SIZE = 1_000

# Orchestrator
MAX_PARALLEL_TOOLS = 100
MAX_ITERATIONS = 50
MAX_SUB_QUERIES = 100


# ============================================================================
# Timeout Configuration (seconds)
# ============================================================================

TIMEOUT_DEFAULT = 30.0
TIMEOUT_LLM = 60.0
TIMEOUT_TOOL = 300.0
TIMEOUT_LONG = 600.0
TIMEOUT_BATCH = 1800.0  # 30 minutes for large batches
