# 🧪 Kea Test Suite

Complete test suite for the Kea Research Engine.

## Test Categories

| Category | Count | API Required | Time |
|----------|-------|--------------|------|
| Unit Tests | 8 | ❌ No | < 1 min |
| Integration Tests | 5 | ✅ Yes | 5-10 min |
| MCP Tool Tests | 4 | ✅ Yes | 5-10 min |
| Stress Tests | 1 | ✅ Yes | 5 min |
| **Total** | **18** | | ~20 min |

---

## 📋 All Tests at a Glance

| # | Test File | Purpose | API? |
|---|-----------|---------|------|
| **Unit Tests** |
| 1 | `unit/test_schemas.py` | Pydantic schemas | ❌ |
| 2 | `unit/test_config.py` | Configuration | ❌ |
| 3 | `unit/test_mcp_protocol.py` | MCP protocol | ❌ |
| 4 | `unit/test_vector_store.py` | Vector store | ❌ |
| 5 | `unit/test_graph_rag.py` | Knowledge graph | ❌ |
| 6 | `unit/test_queue.py` | Queue abstraction | ❌ |
| 7 | `unit/test_registry.py` | Tool registry | ❌ |
| 8 | `unit/test_parallel_executor.py` | Parallel execution | ❌ |
| **Integration Tests** |
| 9 | `integration/test_api_health.py` | Health checks | ✅ |
| 10 | `integration/test_jobs_api.py` | Job CRUD | ✅ |
| 11 | `integration/test_llm_api.py` | LLM management | ✅ |
| 12 | `integration/test_mcp_api.py` | MCP tools | ✅ |
| 13 | `integration/test_system_api.py` | System info | ✅ |
| **MCP Tool Tests** |
| 14 | `mcp/test_scraper_tools.py` | fetch_url, batch_scrape | ✅ |
| 15 | `mcp/test_search_tools.py` | web_search, news_search | ✅ |
| 16 | `mcp/test_python_tools.py` | execute_code, sql_query | ✅ |
| 17 | `mcp/test_analysis_tools.py` | meta_analysis, trend | ✅ |
| **Stress Tests** |
| 18 | `stress/test_concurrent_requests.py` | Load testing | ✅ |

---

## 🚀 Quick Start

### 1. Run Unit Tests (No API)
```bash
pytest tests/unit -v
```

### 2. Start API Then Run Integration Tests
```bash
# Terminal 1
python -m services.api_gateway.main

# Terminal 2
pytest tests/integration -v -m integration
```

### 3. Run All Tests
```bash
pytest tests -v
```

### 4. Run Specific Category
```bash
# Only MCP tool tests
pytest tests/mcp -v -m mcp

# Only stress tests
pytest tests/stress -v -m stress
```

---

## 📁 Directory Structure

```
tests/
├── unit/                   # No API required
│   ├── test_schemas.py
│   ├── test_config.py
│   ├── test_mcp_protocol.py
│   ├── test_vector_store.py
│   ├── test_graph_rag.py
│   ├── test_queue.py
│   ├── test_registry.py
│   └── test_parallel_executor.py
├── integration/            # API required
│   ├── test_api_health.py
│   ├── test_jobs_api.py
│   ├── test_llm_api.py
│   ├── test_mcp_api.py
│   └── test_system_api.py
├── mcp/                    # MCP tool tests
│   ├── test_scraper_tools.py
│   ├── test_search_tools.py
│   ├── test_python_tools.py
│   └── test_analysis_tools.py
├── stress/                 # Load tests
│   └── test_concurrent_requests.py
├── conftest.py             # Fixtures
└── README.md
```

---

## ✅ Recommended Test Sequence

### For Development
```bash
pytest tests/unit -v
```

### For Pre-Commit
```bash
pytest tests/unit tests/integration -v
```

### For Release
```bash
pytest tests -v --tb=short
```
