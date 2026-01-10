# 🧪 Kea Test Suite

Complete test suite for the Kea Research Engine.

---

## 📊 Test Coverage Summary

| Category | Tests | API Required | Time |
|----------|:-----:|:------------:|:----:|
| Unit Tests | 23 | ❌ | < 3 min |
| Integration Tests | 11 | ✅ | 10-15 min |
| MCP Tool Tests | 5 | ✅ | 5-10 min |
| Simulation Tests | 1 | ❌ | 2-3 min |
| Stress Tests | 1 | ✅ | 5 min |
| **Total** | **41** | | ~35 min |

---

## 🚀 Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run unit tests (no API)
pytest tests/unit -v

# Run simulation tests (no API - good for Colab/Kaggle)
pytest tests/simulation -v

# Run integration tests (start API first)
python -m services.api_gateway.main  # Terminal 1
pytest tests/integration -v           # Terminal 2
```

---

## 📋 Complete Test List

### Unit Tests (`tests/unit/`) - 23 Tests

| # | File | Component | Tests |
|---|------|-----------|-------|
| 1 | `test_schemas.py` | Pydantic models | AtomicFact, Source, JobRequest |
| 2 | `test_config.py` | Configuration | Settings singleton |
| 3 | `test_mcp_protocol.py` | JSON-RPC protocol | Request/Response models |
| 4 | `test_mcp_client.py` | MCP client | Client, transport, server base |
| 5 | `test_mcp_tools.py` | Tool functions | Direct tool calls |
| 6 | `test_python_tools.py` | Python tools | SQL query, dataframe ops |
| 7 | `test_vector_store.py` | Vector store | Add, search, delete |
| 8 | `test_fact_store.py` | Fact store | CRUD operations |
| 9 | `test_artifact_store.py` | Artifact store | Save, load, delete |
| 10 | `test_graph_rag.py` | Knowledge graph | Entities, facts, provenance |
| 11 | `test_queue.py` | Queue | Push, pop, ack |
| 12 | `test_registry.py` | Tool registry | Register, get, stats |
| 13 | `test_parallel_executor.py` | Parallel exec | Concurrent tool calls |
| 14 | `test_checkpointing.py` | State persistence | Save, load, delete |
| 15 | `test_graph.py` | LangGraph | State machine, nodes |
| 16 | `test_embedding.py` | Qwen3 embeddings | OpenRouter, local |
| 17 | `test_llm_client.py` | LLM client | Initialization |
| 18 | `test_llm_provider.py` | LLM provider | Provider classes |
| 19 | `test_logging.py` | Structured logging | Logger, decorators |
| 20 | `test_metrics.py` | Prometheus metrics | Recording, middleware |
| 21 | `test_workers.py` | Workers | All 3 workers |
| 22 | `mcp_servers/test_servers.py` | MCP servers | Server initialization |
| 23 | `orchestrator/test_orchestrator.py` | Orchestrator | Service lifecycle |

```bash
pytest tests/unit -v
```

---

### Integration Tests (`tests/integration/`) - 11 Tests

| # | File | Endpoints | Tests |
|---|------|-----------|-------|
| 1 | `test_api_health.py` | `/health`, `/docs` | Health, docs, metrics |
| 2 | `test_jobs_api.py` | `/api/v1/jobs/*` | Create, list, status, cancel |
| 3 | `test_llm_api.py` | `/api/v1/llm/*` | Providers, models, usage |
| 4 | `test_mcp_api.py` | `/api/v1/mcp/*` | Servers, tools, invoke |
| 5 | `test_system_api.py` | `/api/v1/system/*` | Capabilities, config |
| 6 | `test_memory_api.py` | `/api/v1/memory/*` | Facts, search, entities |
| 7 | `test_artifacts_api.py` | `/api/v1/artifacts/*` | Upload, download, list |
| 8 | `test_graph_api.py` | `/api/v1/graph/*` | Entities, provenance |
| 9 | `test_interventions_api.py` | `/api/v1/interventions/*` | HITL workflow |
| 10 | `test_pipeline.py` | Full pipeline | Multi-step research |
| 11 | `test_e2e.py` | Complete E2E | All components together |

```bash
python -m services.api_gateway.main  # Start API
pytest tests/integration -v
```

---

### MCP Tool Tests (`tests/mcp/`) - 5 Tests

| # | File | Tools |
|---|------|-------|
| 1 | `test_scraper_tools.py` | `fetch_url`, `batch_scrape` |
| 2 | `test_search_tools.py` | `web_search`, `news_search`, `academic_search` |
| 3 | `test_python_tools.py` | `execute_code`, `sql_query`, `dataframe_ops` |
| 4 | `test_analysis_tools.py` | `meta_analysis`, `trend_detection` |
| 5 | `test_vision_tools.py` | `table_ocr`, `chart_reader` |

```bash
pytest tests/mcp -v -m mcp
```

---

### Simulation Tests (`tests/simulation/`) - 1 Test

| # | File | Description |
|---|------|-------------|
| 1 | `test_research_simulation.py` | Complete research flow simulation |

> 🎯 **Best for Colab/Kaggle** - No API required, tests state machine and data models.

```bash
pytest tests/simulation -v -m simulation
```

**Contents:**
- `TestResearchSimulation` - Full research query simulation
- `TestEmbeddingSimulation` - Embedding provider selection
- `TestGraphRAGSimulation` - Knowledge graph building

---

### Stress Tests (`tests/stress/`) - 1 Test

| # | File | Description |
|---|------|-------------|
| 1 | `test_concurrent_requests.py` | Concurrent API load testing |

```bash
pytest tests/stress -v -m stress
```

---

## 🔧 Coverage Matrix

| Component | Unit | Integration | Simulation |
|:----------|:----:|:-----------:|:----------:|
| shared/schemas | ✅ | - | ✅ |
| shared/config | ✅ | - | - |
| shared/logging | ✅ | - | - |
| shared/mcp | ✅ | ✅ | - |
| shared/queue | ✅ | - | - |
| shared/llm | ✅ | ✅ | - |
| shared/embedding | ✅ | - | ✅ |
| rag_service/vector_store | ✅ | - | - |
| rag_service/fact_store | ✅ | ✅ | - |
| rag_service/artifact_store | ✅ | ✅ | - |
| rag_service/graph_rag | ✅ | ✅ | ✅ |
| orchestrator/registry | ✅ | ✅ | - |
| orchestrator/executor | ✅ | - | - |
| orchestrator/checkpointing | ✅ | - | - |
| orchestrator/graph | ✅ | - | ✅ |
| api_gateway (8 routes) | - | ✅ | - |
| workers (3) | ✅ | - | - |
| mcp_servers (5) | ✅ | ✅ | - |
| mcp_tools (14) | ✅ | ✅ | - |

**Coverage: 100%**

---

## 📁 Directory Structure

```
tests/
├── unit/                          # 23 files
│   ├── mcp_servers/
│   │   └── test_servers.py
│   ├── orchestrator/
│   │   └── test_orchestrator.py
│   ├── test_schemas.py
│   ├── test_config.py
│   ├── test_mcp_protocol.py
│   ├── test_mcp_client.py
│   ├── test_mcp_tools.py
│   ├── test_python_tools.py
│   ├── test_vector_store.py
│   ├── test_fact_store.py
│   ├── test_artifact_store.py
│   ├── test_graph_rag.py
│   ├── test_queue.py
│   ├── test_registry.py
│   ├── test_parallel_executor.py
│   ├── test_checkpointing.py
│   ├── test_graph.py
│   ├── test_embedding.py
│   ├── test_llm_client.py
│   ├── test_llm_provider.py
│   ├── test_logging.py
│   ├── test_metrics.py
│   └── test_workers.py
├── integration/                   # 11 files
│   ├── test_api_health.py
│   ├── test_jobs_api.py
│   ├── test_llm_api.py
│   ├── test_mcp_api.py
│   ├── test_system_api.py
│   ├── test_memory_api.py
│   ├── test_artifacts_api.py
│   ├── test_graph_api.py
│   ├── test_interventions_api.py
│   ├── test_pipeline.py
│   └── test_e2e.py
├── mcp/                           # 5 files
│   ├── test_scraper_tools.py
│   ├── test_search_tools.py
│   ├── test_python_tools.py
│   ├── test_analysis_tools.py
│   └── test_vision_tools.py
├── simulation/                    # 1 file
│   └── test_research_simulation.py
├── stress/                        # 1 file
│   └── test_concurrent_requests.py
├── conftest.py
└── README.md
```

---

## ✅ Recommended Sequences

| Purpose | Command |
|:--------|:--------|
| Quick Check | `pytest tests/unit -v -x` |
| Colab/Kaggle | `pytest tests/unit tests/simulation -v` |
| Pre-Commit | `pytest tests/unit tests/integration -v` |
| Full Suite | `pytest tests -v --tb=short` |
| Coverage | `pytest tests --cov=shared --cov=services` |

---

## 🧪 Colab/Kaggle Testing

```python
# Install
!pip install -e ".[dev]"

# Run simulation tests (no API needed)
!pytest tests/simulation -v

# Test embeddings
from shared.embedding import LocalEmbedding
provider = LocalEmbedding(device="cuda")
embeddings = await provider.embed(["Test text"])

# Test reranker
from shared.embedding import LocalReranker
reranker = LocalReranker(device="cuda")
results = await reranker.rerank("query", ["doc1", "doc2"])
```
