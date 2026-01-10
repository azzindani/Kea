# 🦜 Kea: Distributed Autonomous Research Engine (DARE)

> **"Not just a Chatbot. A Research Factory."**

---

## � MCP Tool Calling Standard

Kea adopts the **Model Context Protocol (MCP)** as its universal tool calling interface. MCP enables:

- **Parallel Tool Execution:** Multiple MCP servers run simultaneously, allowing the orchestrator to invoke scraping, analysis, and vision tools concurrently
- **Standardized Communication:** JSON-RPC 2.0 over stdio/SSE provides consistent request/response patterns across all tools
- **Dynamic Discovery:** Tools self-register their capabilities, allowing hot-swapping and runtime extension
- **Isolated Execution:** Each MCP server runs in its own process/container, ensuring fault isolation

### MCP Architecture Overview

```mermaid
graph TD
    %% --- STYLES ---
    classDef orchestrator fill:#2d3436,stroke:#fff,stroke-width:2px,color:#fff;
    classDef mcp fill:#0984e3,stroke:#fff,stroke-width:2px,color:#fff;
    classDef tool fill:#00b894,stroke:#333,stroke-width:2px,color:#fff;
    classDef transport fill:#fdcb6e,stroke:#333,stroke-width:2px,color:#333;

    %% --- THE BRAIN ---
    Orchestrator["🧠 Orchestrator<br/>(MCP Client)"]:::orchestrator

    %% --- MCP TRANSPORT LAYER ---
    subgraph MCPLayer ["MCP Transport Layer (JSON-RPC 2.0)"]
        Router{{"🔀 MCP Router<br/>(Parallel Dispatcher)"}}:::mcp
        
        Router -->|stdio| MCP1["🕷️ Scraper Server"]:::mcp
        Router -->|stdio| MCP2["🐍 Python Server"]:::mcp
        Router -->|stdio| MCP3["👁️ Vision Server"]:::mcp
        Router -->|SSE| MCP4["📊 Analysis Server"]:::mcp
        Router -->|stdio| MCP5["🔍 Search Server"]:::mcp
    end

    %% --- TOOL IMPLEMENTATIONS ---
    subgraph Tools ["Tool Implementations"]
        MCP1 --> T1["Playwright<br/>BeautifulSoup"]:::tool
        MCP2 --> T2["Pandas<br/>DuckDB"]:::tool
        MCP3 --> T3["GPT-4o Vision<br/>Gemini Vision"]:::tool
        MCP4 --> T4["Statistical<br/>ML Models"]:::tool
        MCP5 --> T5["Tavily<br/>Brave Search"]:::tool
    end

    %% --- CONNECTIONS ---
    Orchestrator -->|"tools/list"| Router
    Orchestrator -->|"tools/call (parallel)"| Router
    
    %% --- RESPONSE FLOW ---
    T1 -->|Result| MCP1
    T2 -->|Result| MCP2
    T3 -->|Result| MCP3
    T4 -->|Result| MCP4
    T5 -->|Result| MCP5
```

### MCP Message Flow

```
┌─────────────────┐    JSON-RPC 2.0    ┌─────────────────┐
│   Orchestrator  │ ←───────────────→  │   MCP Server    │
│   (MCP Client)  │                    │   (Tool Host)   │
└─────────────────┘                    └─────────────────┘
        │                                      │
        │  1. initialize                       │
        │  ─────────────────────────────────→  │
        │                                      │
        │  2. tools/list (discover)            │
        │  ─────────────────────────────────→  │
        │  ←─────────────────────────────────  │
        │     [{name, description, schema}]    │
        │                                      │
        │  3. tools/call (parallel batch)      │
        │  ─────────────────────────────────→  │
        │  ─────────────────────────────────→  │ (concurrent)
        │  ─────────────────────────────────→  │
        │                                      │
        │  4. results (streamed/batched)       │
        │  ←─────────────────────────────────  │
        │  ←─────────────────────────────────  │
        │  ←─────────────────────────────────  │
        │                                      │
```

### Key MCP Benefits for Kea

| Feature | Benefit |
|:--------|:--------|
| **Parallel Execution** | Scrape 10 URLs while running Python analysis simultaneously |
| **Tool Isolation** | Crashing scraper doesn't affect Python executor |
| **Schema Validation** | JSON Schema ensures type-safe tool invocations |
| **Progress Streaming** | Long-running tools report incremental progress |
| **Resource Management** | MCP servers can be scaled independently |
| **Hot Reload** | Add new tools without restarting orchestrator |

---

## 📝 Naming Conventions & Standards

### Code Naming Rules

> ⚠️ **IMPORTANT:** Do NOT use "Kea" in any code, function names, class names, variable names, or directory names. Use generic, descriptive names instead.

| Element | ❌ Avoid | ✅ Use |
|:--------|:---------|:-------|
| **Directories** | `kea/`, `kea_service/` | `services/`, `core/`, `shared/` |
| **Classes** | `KeaOrchestrator`, `KeaClient` | `Orchestrator`, `MCPClient` |
| **Functions** | `kea_search()`, `run_kea()` | `search()`, `run_research()` |
| **Variables** | `kea_config`, `kea_result` | `config`, `research_result` |
| **Modules** | `kea_utils.py` | `utils.py`, `helpers.py` |

### Configuration Management

| File | Purpose | Git |
|:-----|:--------|:---:|
| `.env` | Secrets (API keys, passwords) | ❌ Ignored |
| `.env.example` | Template for `.env` | ✅ Committed |
| `configs/settings.yaml` | Application settings | ✅ Committed |
| `configs/mcp_servers.yaml` | MCP server registry | ✅ Committed |
| `configs/logging.yaml` | Logging configuration | ✅ Committed |
| `configs/vocab/*.yaml` | Vocabulary & prompts | ✅ Committed |

### Environment Variables

```bash
# LLM Provider
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=nvidia/nemotron-3-nano-30b-a3b:free

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dare
REDIS_URL=redis://localhost:6379

# Mode
ENVIRONMENT=development  # development | staging | production
LOG_LEVEL=DEBUG
```

### Vocabulary List (configs/vocab/)

```yaml
# configs/vocab/domains.yaml - Domain terminology
mining:
  entities: ["nickel", "coal", "copper"]
  sources: ["esdm.go.id"]

# configs/vocab/prompts.yaml - Prompt templates  
roles:
  generator: "You are a thorough research assistant..."
  critic: "You are a skeptical fact-checker..."
```

---

## �📁 Project Directory Structure

```
kea/
├── 📁 services/                              # Microservices (The Core)
│   │
│   ├── 📁 orchestrator/                      # 🧠 The Brain - Main Orchestrator (MCP Client)
│   │   ├── __init__.py
│   │   ├── main.py                           # FastAPI entrypoint
│   │   ├── config.py                         # Environment & mode detection
│   │   ├── 📁 core/
│   │   │   ├── __init__.py
│   │   │   ├── graph.py                      # LangGraph cyclic state machine
│   │   │   ├── router.py                     # Intention Router (Path A/B/C/D)
│   │   │   └── consensus.py                  # Adversarial Collaboration Engine
│   │   ├── 📁 mcp/                           # ⚡ MCP Client Implementation
│   │   │   ├── __init__.py
│   │   │   ├── client.py                     # MCP Client (JSON-RPC 2.0)
│   │   │   ├── registry.py                   # Tool registry & discovery
│   │   │   ├── parallel_executor.py          # Parallel tool invocation manager
│   │   │   └── session_manager.py            # MCP session lifecycle
│   │   ├── 📁 nodes/                         # LangGraph Nodes
│   │   │   ├── __init__.py
│   │   │   ├── planner.py                    # 📝 Planner & Decomposer
│   │   │   ├── keeper.py                     # 🛡️ The Keeper (Context Guard)
│   │   │   ├── divergence.py                 # ✨ Divergence Engine (Abductive)
│   │   │   ├── synthesizer.py                # ✍️ Report Synthesizer
│   │   │   └── architect.py                  # 🏗️ Meta-Prompt Layer
│   │   ├── 📁 agents/                        # Specialized Worker Agents
│   │   │   ├── __init__.py
│   │   │   ├── generator.py                  # 🤠 The Optimist
│   │   │   ├── critic.py                     # 🧐 The Pessimist
│   │   │   └── judge.py                      # ⚖️ The Synthesizer
│   │   └── 📁 state/
│   │       ├── __init__.py
│   │       └── models.py                     # Pydantic state schemas
│   │
│   ├── 📁 rag_service/                       # 💾 The Memory Vault
│   │   ├── __init__.py
│   │   ├── main.py                           # FastAPI/gRPC entrypoint
│   │   ├── config.py
│   │   ├── 📁 core/
│   │   │   ├── __init__.py
│   │   │   ├── vector_store.py               # Qdrant/Chroma abstraction
│   │   │   ├── graph_store.py                # GraphRAG relationships
│   │   │   └── artifact_store.py             # S3/Parquet blob storage
│   │   ├── 📁 schemas/
│   │   │   ├── __init__.py
│   │   │   ├── atomic_fact.py                # Atomic Fact Schema
│   │   │   └── session.py                    # Conversation Project Schema
│   │   └── 📁 api/
│   │       ├── __init__.py
│   │       ├── search.py                     # Semantic search endpoints
│   │       ├── provenance.py                 # Provenance graph endpoints
│   │       └── artifacts.py                  # Artifact download/preview
│   │
│   └── 📁 api_gateway/                       # 🚪 The Front Door
│       ├── __init__.py
│       ├── main.py                           # FastAPI gateway
│       ├── config.py
│       ├── 📁 routes/
│       │   ├── __init__.py
│       │   ├── jobs.py                       # /api/v1/jobs (Job Dispatcher)
│       │   ├── memory.py                     # /api/v1/memory (Knowledge Brain)
│       │   ├── artifacts.py                  # /api/v1/artifacts
│       │   ├── interventions.py              # /api/v1/interventions (HITL)
│       │   ├── system.py                     # /api/v1/system (Capabilities)
│       │   ├── llm.py                        # /api/v1/llm (Provider Management)
│       │   └── mcp.py                        # /api/v1/mcp (Tool Management)
│       ├── 📁 middleware/
│       │   ├── __init__.py
│       │   ├── auth.py                       # JWT Bearer Token
│       │   ├── rate_limit.py                 # API rate limiting
│       │   └── request_id.py                 # Request correlation IDs
│       └── 📁 schemas/
│           ├── __init__.py
│           ├── job.py                        # Job request/response models
│           └── response.py                   # Standard API responses
│
├── 📁 mcp_servers/                           # 🔌 MCP Tool Servers (Parallel Hands)
│   │
│   ├── 📁 scraper_server/                    # 🕷️ Web Scraping MCP Server
│   │   ├── __init__.py
│   │   ├── server.py                         # MCP server entrypoint (stdio/SSE)
│   │   ├── config.py
│   │   ├── 📁 tools/
│   │   │   ├── __init__.py
│   │   │   ├── fetch_url.py                  # Simple HTTP fetch
│   │   │   ├── browser_scrape.py             # Playwright headless scraping
│   │   │   ├── batch_scrape.py               # Parallel URL batch processing
│   │   │   └── pdf_extract.py                # PDF text/table extraction
│   │   ├── 📁 stealth/
│   │   │   ├── __init__.py
│   │   │   ├── proxy_rotator.py              # Residential proxy management
│   │   │   ├── ua_rotator.py                 # User-Agent spoofing
│   │   │   ├── fingerprint.py                # Browser fingerprint randomization
│   │   │   └── rate_limiter.py               # Domain-level throttling
│   │   └── manifest.json                     # MCP tool definitions
│   │
│   ├── 📁 python_server/                     # 🐍 Python Execution MCP Server
│   │   ├── __init__.py
│   │   ├── server.py                         # MCP server entrypoint
│   │   ├── config.py
│   │   ├── 📁 tools/
│   │   │   ├── __init__.py
│   │   │   ├── execute_code.py               # Sandboxed Python execution
│   │   │   ├── dataframe_ops.py              # Pandas DataFrame operations
│   │   │   ├── sql_query.py                  # DuckDB SQL queries
│   │   │   └── statistical.py                # Statistical analysis functions
│   │   ├── 📁 sandbox/
│   │   │   ├── __init__.py
│   │   │   ├── docker_runner.py              # Docker container isolation
│   │   │   ├── e2b_runner.py                 # E2B cloud sandbox
│   │   │   └── local_runner.py               # Local subprocess (dev only)
│   │   └── manifest.json                     # MCP tool definitions
│   │
│   ├── 📁 vision_server/                     # �️ Vision/OCR MCP Server
│   │   ├── __init__.py
│   │   ├── server.py                         # MCP server entrypoint
│   │   ├── config.py
│   │   ├── 📁 tools/
│   │   │   ├── __init__.py
│   │   │   ├── screenshot_extract.py         # Screenshot → structured data
│   │   │   ├── chart_reader.py               # Chart/graph interpretation
│   │   │   ├── table_ocr.py                  # Table structure extraction
│   │   │   └── document_vision.py            # Full document understanding
│   │   └── manifest.json                     # MCP tool definitions
│   │
│   ├── 📁 search_server/                     # 🔍 Web Search MCP Server
│   │   ├── __init__.py
│   │   ├── server.py                         # MCP server entrypoint
│   │   ├── config.py
│   │   ├── 📁 tools/
│   │   │   ├── __init__.py
│   │   │   ├── web_search.py                 # Tavily/Brave/SerpAPI search
│   │   │   ├── news_search.py                # News-specific search
│   │   │   ├── academic_search.py            # Semantic Scholar/arXiv
│   │   │   └── site_search.py                # Domain-restricted search
│   │   └── manifest.json                     # MCP tool definitions
│   │
│   ├── 📁 analysis_server/                   # 📊 Analysis MCP Server
│   │   ├── __init__.py
│   │   ├── server.py                         # MCP server entrypoint (SSE for streaming)
│   │   ├── config.py
│   │   ├── 📁 tools/
│   │   │   ├── __init__.py
│   │   │   ├── meta_analysis.py              # Cross-source meta-analysis
│   │   │   ├── trend_detection.py            # Time-series trend analysis
│   │   │   ├── anomaly_detection.py          # Outlier/anomaly detection
│   │   │   └── comparative.py                # Comparative analysis tools
│   │   └── manifest.json                     # MCP tool definitions
│   │
│   └── 📁 _template_server/                  # 📝 Template for new MCP servers
│       ├── __init__.py
│       ├── server.py                         # Boilerplate MCP server
│       ├── config.py
│       ├── 📁 tools/
│       │   ├── __init__.py
│       │   └── example_tool.py               # Example tool implementation
│       └── manifest.json                     # MCP tool schema template
│
├── 📁 shared/                                # Shared Utilities & Contracts
│   ├── __init__.py
│   ├── 📁 mcp/                               # 🔌 MCP SDK & Utilities
│   │   ├── __init__.py
│   │   ├── protocol.py                       # JSON-RPC 2.0 message types
│   │   ├── transport.py                      # stdio/SSE transport abstractions
│   │   ├── server_base.py                    # Base MCP server class
│   │   ├── client_base.py                    # Base MCP client class
│   │   └── schemas.py                        # Tool/Resource/Prompt schemas
│   ├── 📁 llm/
│   │   ├── __init__.py
│   │   ├── provider.py                       # LLM provider abstraction
│   │   ├── openai.py
│   │   ├── gemini.py
│   │   └── anthropic.py
│   ├── 📁 queue/
│   │   ├── __init__.py
│   │   ├── base.py                           # Queue abstraction
│   │   ├── redis_queue.py                    # Production Redis queue
│   │   └── memory_queue.py                   # Local threading queue
│   ├── 📁 storage/
│   │   ├── __init__.py
│   │   ├── base.py                           # Storage abstraction
│   │   ├── s3.py                             # S3/MinIO storage
│   │   └── local.py                          # Local filesystem
│   ├── 📁 database/
│   │   ├── __init__.py
│   │   ├── base.py                           # DB abstraction
│   │   ├── postgres.py                       # Production PostgreSQL
│   │   └── sqlite.py                         # Local SQLite
│   └── 📁 logging/                           # 📊 Standardized Logging Infrastructure
│       ├── __init__.py
│       ├── config.py                         # Logging configuration
│       ├── structured.py                     # Structured JSON logging
│       ├── context.py                        # Context propagation (trace_id, span_id)
│       ├── formatters.py                     # Log formatters (JSON, Console, File)
│       ├── handlers.py                       # Custom log handlers
│       ├── middleware.py                     # FastAPI/MCP logging middleware
│       ├── decorators.py                     # @log_execution, @trace decorators
│       ├── metrics.py                        # Prometheus metrics integration
│       └── exporters.py                      # OpenTelemetry exporters (Jaeger, Zipkin)
│
├── 📁 workers/                               # Background Job Workers
│   ├── __init__.py
│   ├── research_worker.py                    # Deep Research job processor
│   ├── synthesis_worker.py                   # Grand Synthesis job processor
│   └── shadow_lab_worker.py                  # Shadow Lab job processor
│
├── 📁 tests/                                 # Test Suite
│   ├── 📁 unit/
│   │   ├── 📁 orchestrator/
│   │   │   ├── test_router.py
│   │   │   ├── test_planner.py
│   │   │   ├── test_keeper.py
│   │   │   ├── test_consensus.py
│   │   │   └── test_mcp_client.py            # MCP client tests
│   │   ├── 📁 mcp_servers/
│   │   │   ├── test_scraper_server.py
│   │   │   ├── test_python_server.py
│   │   │   ├── test_vision_server.py
│   │   │   └── test_search_server.py
│   │   ├── 📁 rag_service/
│   │   │   ├── test_vector_store.py
│   │   │   └── test_artifact_store.py
│   │   └── 📁 shared/
│   │       ├── test_logging.py               # Logging infrastructure tests
│   │       └── test_mcp_protocol.py          # MCP protocol tests
│   ├── 📁 integration/
│   │   ├── test_job_lifecycle.py             # Full job flow (submit → complete)
│   │   ├── test_memory_fork.py               # Path A: Incremental research
│   │   ├── test_shadow_lab.py                # Path B: Recalculation
│   │   ├── test_grand_synthesis.py           # Path C: Meta-analysis
│   │   ├── test_deep_research.py             # Path D: Zero-shot
│   │   ├── test_mcp_parallel.py              # Parallel MCP tool execution
│   │   └── test_logging_pipeline.py          # End-to-end logging tests
│   ├── 📁 e2e/
│   │   ├── test_api_gateway.py               # Full API flow tests
│   │   ├── test_human_intervention.py        # HITL workflow tests
│   │   └── test_checkpoint_recovery.py       # Crash recovery tests
│   ├── 📁 fixtures/
│   │   ├── sample_documents/                 # Test PDFs, CSVs
│   │   ├── mock_responses/                   # Mocked LLM/API responses
│   │   ├── parquet_samples/                  # Sample artifact files
│   │   └── mcp_mocks/                        # Mocked MCP server responses
│   └── conftest.py                           # Pytest fixtures & configuration
│
├── 📁 scripts/                               # Utility Scripts
│   ├── setup_local.py                        # Local development setup
│   ├── run_tests.py                          # Test runner with coverage
│   ├── migrate_db.py                         # Database migration script
│   ├── start_mcp_servers.py                  # Launch all MCP servers
│   └── log_viewer.py                         # CLI log viewer/analyzer
│
├── 📁 deployment/                            # Deployment Configurations
│   ├── 📁 docker/
│   │   ├── Dockerfile.orchestrator
│   │   ├── Dockerfile.rag
│   │   ├── Dockerfile.gateway
│   │   ├── Dockerfile.mcp-scraper
│   │   ├── Dockerfile.mcp-python
│   │   ├── Dockerfile.mcp-vision
│   │   ├── Dockerfile.mcp-search
│   │   └── Dockerfile.mcp-analysis
│   ├── docker-compose.yml                    # Full stack local
│   ├── docker-compose.dev.yml                # Development overrides
│   ├── docker-compose.mcp.yml                # MCP servers only
│   ├── 📁 k8s/                               # Kubernetes manifests
│   │   ├── orchestrator.yaml
│   │   ├── rag-service.yaml
│   │   ├── mcp-servers.yaml                  # MCP server deployments
│   │   ├── logging-stack.yaml                # Loki/Promtail/Grafana
│   │   └── ingress.yaml
│   └── 📁 logging/                           # Logging Infrastructure Configs
│       ├── promtail-config.yaml              # Log collection
│       ├── loki-config.yaml                  # Log aggregation
│       ├── grafana-dashboards/               # Pre-built dashboards
│       │   ├── mcp-tools.json
│       │   ├── orchestrator.json
│       │   └── api-gateway.json
│       └── alerting-rules.yaml               # Alert definitions
│
├── 📁 docs/                                  # Extended Documentation
│   ├── ARCHITECTURE.md                       # Detailed architecture (mirror)
│   ├── API_REFERENCE.md                      # Full API documentation
│   ├── MCP_GUIDE.md                          # MCP tool development guide
│   ├── LOGGING_GUIDE.md                      # Logging standards & usage
│   ├── DEVELOPMENT.md                        # Developer guide
│   └── DEPLOYMENT.md                         # Production deployment guide
│
├── 📁 configs/                               # Configuration Files
│   ├── mcp_servers.yaml                      # MCP server registry
│   ├── logging.yaml                          # Logging configuration
│   └── rate_limits.yaml                      # Rate limiting rules
│
├── .env.example                              # Environment template
├── pyproject.toml                            # Python dependencies (Poetry)
├── README.md                                 # This file
└── Makefile                                  # Common development commands
```

---

## 📋 Development Plan

### Phase 0: Foundation Setup *(Week 1)*
**Goal:** Establish project scaffolding, core abstractions, and logging infrastructure.

| Task | Description | Priority |
|:-----|:------------|:--------:|
| Initialize project structure | Create all directories & `__init__.py` files | 🔴 Critical |
| Setup `pyproject.toml` | Define dependencies (LangGraph, FastAPI, MCP SDK, etc.) | 🔴 Critical |
| Create shared abstractions | Implement `shared/` modules for LLM, Queue, Storage, DB | 🔴 Critical |
| **Setup logging infrastructure** | Implement `shared/logging/` with structured JSON logging | 🔴 Critical |
| **Configure OpenTelemetry** | Setup trace/span context propagation | 🔴 Critical |
| Environment configuration | Build `config.py` with local/production mode detection | 🔴 Critical |
| Create base Pydantic schemas | Define state models, API schemas, and contracts | 🟡 High |
| **MCP SDK base classes** | Implement `shared/mcp/` with protocol and transport | 🟡 High |

**Deliverables:**
- [ ] Working project structure with all directories
- [ ] `pyproject.toml` with pinned dependencies
- [ ] Shared abstractions for LLM, Queue, Storage, Database
- [ ] **Structured logging with JSON output and trace correlation**
- [ ] **MCP protocol types and base classes**
- [ ] Environment-aware configuration system

---

### Phase 1: Logging & Observability Infrastructure *(Week 1-2)*
**Goal:** Establish comprehensive logging, metrics, and tracing before building features.

| Task | Description | Priority |
|:-----|:------------|:--------:|
| Implement structured logger | JSON logging with configurable formatters | 🔴 Critical |
| Context propagation | trace_id, span_id, request_id across services | � Critical |
| Logging middleware | FastAPI middleware for request/response logging | 🔴 Critical |
| MCP logging middleware | Tool call logging with timing and results | 🔴 Critical |
| Metrics integration | Prometheus metrics for latency, errors, throughput | 🟡 High |
| Log decorators | `@log_execution`, `@trace` for function logging | 🟡 High |
| OpenTelemetry exporters | Jaeger/Zipkin trace export | 🟡 High |
| Log aggregation config | Loki/Promtail configuration for deployment | 🟢 Medium |
| Grafana dashboards | Pre-built dashboards for MCP, API, Orchestrator | � Medium |

**Deliverables:**
- [ ] Structured JSON logging across all services
- [ ] Distributed tracing with OpenTelemetry
- [ ] Prometheus metrics endpoint
- [ ] Pre-built Grafana dashboards
- [ ] Logging documentation (LOGGING_GUIDE.md)

**Log Schema Standard:**
```json
{
  "timestamp": "2026-01-10T19:00:00.000Z",
  "level": "INFO",
  "service": "orchestrator",
  "trace_id": "abc123",
  "span_id": "def456",
  "request_id": "req-789",
  "message": "Tool execution completed",
  "context": {
    "tool_name": "web_scraper",
    "mcp_server": "scraper_server",
    "duration_ms": 1234,
    "result_size_bytes": 5678
  }
}
```

---

### Phase 2: MCP Tool Servers *(Week 2-3)*
**Goal:** Build parallel-capable MCP tool servers for all "Hands" functionality.

| Task | Description | Priority |
|:-----|:------------|:--------:|
| **MCP Server Base** | Implement `shared/mcp/server_base.py` with JSON-RPC 2.0 | 🔴 Critical |
| **Scraper MCP Server** | Web scraping tools with Playwright/BeautifulSoup | 🔴 Critical |
| **Python MCP Server** | Sandboxed Python execution with Pandas/DuckDB | 🔴 Critical |
| **Search MCP Server** | Web search tools (Tavily, Brave, SerpAPI) | 🔴 Critical |
| Vision MCP Server | Screenshot/OCR extraction with GPT-4o/Gemini | 🟡 High |
| Analysis MCP Server | Statistical analysis and trend detection | 🟡 High |
| Stealth infrastructure | Proxy rotation, UA spoofing, rate limiting | 🟡 High |
| Sandbox isolation | Docker/E2B runners for code execution | 🟡 High |
| MCP tool manifests | JSON Schema definitions for all tools | 🟡 High |
| Template server | Boilerplate for adding new MCP servers | 🟢 Medium |

**Deliverables:**
- [ ] 5 working MCP servers (Scraper, Python, Search, Vision, Analysis)
- [ ] Parallel execution capability (invoke multiple servers simultaneously)
- [ ] Tool manifests with JSON Schema validation
- [ ] Stealth infrastructure for web scraping
- [ ] MCP development guide (MCP_GUIDE.md)

**MCP Tool Example:**
```python
@mcp_tool(
    name="browser_scrape",
    description="Scrape webpage content using headless browser",
    schema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "format": "uri"},
            "wait_for": {"type": "string", "description": "CSS selector to wait for"},
            "extract_tables": {"type": "boolean", "default": True}
        },
        "required": ["url"]
    }
)
async def browser_scrape(url: str, wait_for: str = None, extract_tables: bool = True):
    # Implementation with integrated logging
    logger.info("Starting browser scrape", extra={"url": url})
    ...
```

---

### Phase 3: Core Orchestrator with MCP Client *(Week 3-4)*
**Goal:** Build the central "Brain" with LangGraph state machine and MCP client.

| Task | Description | Priority |
|:-----|:------------|:--------:|
| Implement LangGraph graph | Build cyclic state machine with checkpointing | 🔴 Critical |
| **MCP Client implementation** | Connect to MCP servers via JSON-RPC 2.0 | 🔴 Critical |
| **Parallel executor** | Invoke multiple MCP tools concurrently | 🔴 Critical |
| **Tool registry** | Dynamic tool discovery via `tools/list` | 🔴 Critical |
| Create Intention Router | Classify queries into Path A/B/C/D | 🔴 Critical |
| Build Planner node | Query decomposition into atomic facts | 🔴 Critical |
| Build Keeper node | Context drift detection (cosine similarity) | � High |
| Build Divergence Engine | Hypothesis verification & abductive reasoning | 🟡 High |
| Build Synthesizer node | Report generation from validated facts | 🟡 High |
| Implement Meta-Prompt Layer | Dynamic persona injection for workers | 🟡 High |
| Build Consensus Engine | Generator/Critic/Judge adversarial loop | 🟢 Medium |

**Deliverables:**
- [ ] Working LangGraph state machine with OODA loop
- [ ] **MCP Client with parallel tool invocation**
- [ ] **Tool registry with hot-reload capability**
- [ ] Intention Router with 4-path classification
- [ ] All core nodes (Planner, Keeper, Divergence, Synthesizer)
- [ ] Unit tests for each node and MCP client

---

### Phase 4: RAG Service *(Week 4-5)*
**Goal:** Build the "Memory Vault" for atomic facts and artifacts.

| Task | Description | Priority |
|:-----|:------------|:--------:|
| Implement Vector Store | Qdrant/Chroma abstraction with embedding | 🔴 Critical |
| Create Atomic Fact schema | Entity-Attribute-Value-Time-Source structure | 🔴 Critical |
| Implement Artifact Store | S3/Local filesystem for Parquet/Blobs | 🔴 Critical |
| Build GraphRAG layer | Relationship storage between facts | 🟡 High |
| Create Session schema | Conversation Project manifest tracking | 🟡 High |
| Implement semantic search | Query-to-fact similarity matching | 🟡 High |
| Build Provenance Graph API | Node/Edge export for UI visualization | 🟢 Medium |
| Add logging integration | Structured logging for all RAG operations | 🟢 Medium |

**Deliverables:**
- [ ] Vector store with atomic fact ingestion
- [ ] Artifact store with Parquet/blob support
- [ ] Semantic search with confidence scoring
- [ ] Unit tests for all storage operations

---

### Phase 5: API Gateway *(Week 5-6)*
**Goal:** Build the "Front Door" with all API endpoints and MCP management.

| Task | Description | Priority |
|:-----|:------------|:--------:|
| Setup FastAPI gateway | Base server with versioned routing | 🔴 Critical |
| Implement Job Dispatcher | `/jobs` CRUD with polymorphic payloads | 🔴 Critical |
| Implement Memory API | `/memory/search`, `/memory/graph` | 🔴 Critical |
| **Implement MCP API** | `/mcp/servers`, `/mcp/tools`, `/mcp/invoke` | 🔴 Critical |
| Implement Artifacts API | `/artifacts` download/preview | 🟡 High |
| Implement HITL API | `/interventions` pause/resume | 🟡 High |
| Implement System API | `/system/capabilities`, `/system/health` | 🟡 High |
| Implement LLM Management | `/llm/providers`, `/llm/config` | 🟢 Medium |
| Add JWT authentication | Bearer token middleware | 🟢 Medium |
| Add API rate limiting | Request throttling middleware | 🟢 Medium |
| **Request ID middleware** | Correlation ID propagation for distributed tracing | 🟢 Medium |

**Deliverables:**
- [ ] Full REST API with all endpoints documented
- [ ] **MCP management API for tool discovery and invocation**
- [ ] Authentication & authorization middleware
- [ ] OpenAPI/Swagger documentation
- [ ] Integration tests for all routes

---

### Phase 6: Background Workers *(Week 6-7)*
**Goal:** Implement async job processing with checkpointing.

| Task | Description | Priority |
|:-----|:------------|:--------:|
| Setup Redis queue | Job enqueue/dequeue infrastructure | 🔴 Critical |
| Implement Research Worker | Deep research job processor with MCP tools | 🔴 Critical |
| Implement Synthesis Worker | Grand synthesis job processor | 🟡 High |
| Implement Shadow Lab Worker | Recalculation job processor | 🟡 High |
| Add LangGraph checkpointing | PostgreSQL state persistence | 🟡 High |
| Implement crash recovery | Resume from last checkpoint | 🟡 High |
| Add webhook notifications | Callback on job completion | 🟢 Medium |
| **Worker logging** | Structured logging with job context | 🟢 Medium |

**Deliverables:**
- [ ] Background workers with Redis queue
- [ ] Checkpointing and crash recovery
- [ ] All job types processing correctly
- [ ] Integration tests for job lifecycle

---

### Phase 7: Integration & Testing *(Week 7-8)*
**Goal:** End-to-end testing and hardening.

| Task | Description | Priority |
|:-----|:------------|:--------:|
| Write unit tests | Cover all modules >80% | 🔴 Critical |
| Write integration tests | Full job lifecycle flows | 🔴 Critical |
| **MCP integration tests** | Parallel tool execution tests | 🔴 Critical |
| **Logging pipeline tests** | End-to-end trace correlation tests | 🔴 Critical |
| Write E2E tests | API gateway full scenarios | 🟡 High |
| Setup CI/CD pipeline | GitHub Actions for testing | 🟡 High |
| Performance testing | Load testing with Locust | 🟢 Medium |
| Documentation | API reference & developer guide | 🟢 Medium |

**Deliverables:**
- [ ] >80% test coverage
- [ ] **MCP parallel execution tests**
- [ ] **Distributed tracing verification**
- [ ] CI/CD pipeline with automated testing
- [ ] Performance benchmarks
- [ ] Complete documentation

#### 🧪 Standardized Testing Environments

> **Testing Philosophy:** We use **Real Simulation & Case-Based Testing** instead of traditional pytest. Tests are executable notebooks with actual API calls, real data scenarios, and observable outputs that demonstrate system behavior.

All tests are designed to run in cloud notebook environments for reproducibility and GPU access:

| Environment | Primary Use | GPU Access | Notes |
|:------------|:------------|:-----------|:------|
| **Kaggle Notebooks** | Integration & E2E simulations | ✅ Free T4/P100 | 30hr/week GPU quota, persistent datasets |
| **Google Colab** | Component smoke tests | ✅ Free T4 | Easy sharing, quick iteration |
| **Local (Hybrid)** | Development & debugging | ⚡ Optional | Fast feedback, full control |

**Why Real Simulation Over Pytest?**

| Aspect | Traditional Pytest | Real Simulation (Our Approach) |
|:-------|:-------------------|:-------------------------------|
| **Coverage** | Mocked responses | Actual API calls & real data |
| **Debugging** | Stack traces | Visual outputs, logs, artifacts |
| **Reproducibility** | Environment-dependent | Notebook cells = reproducible steps |
| **Documentation** | Separate docs | Test IS the documentation |
| **Observability** | Pass/Fail | Rich outputs, charts, intermediate states |

**Execution Strategy:**

```mermaid
graph LR
    %% --- STYLES ---
    classDef local fill:#00b894,stroke:#333,stroke-width:2px,color:#fff;
    classDef cloud fill:#0984e3,stroke:#fff,stroke-width:2px,color:#fff;
    classDef hybrid fill:#6c5ce7,stroke:#fff,stroke-width:2px,color:#fff;

    %% --- TEST FLOW ---
    Dev["🧑‍💻 Developer"] --> Local["💻 Local Simulation<br/>(Fast Feedback)"]:::local
    Local --> Push["📤 Git Push"]
    Push --> CI["⚙️ GitHub Actions<br/>(Lint + Smoke)"]
    CI --> Kaggle["📊 Kaggle<br/>(Full Simulation)"]:::cloud
    CI --> Colab["🔬 Colab<br/>(Component Tests)"]:::cloud
    
    Kaggle --> Report["📋 Execution Report<br/>(Artifacts + Logs)"]
    Colab --> Report
    
    Report --> Merge["✅ Merge Ready"]
```

**Test Case Distribution:**

| Test Scenario | Local | Colab | Kaggle |
|:--------------|:-----:|:-----:|:------:|
| MCP Server Simulation | ✅ Primary | ✅ | ⚪ |
| Single Tool Execution | ✅ Primary | ✅ | ⚪ |
| Multi-Tool Parallel Simulation | ⚪ | ✅ | ✅ Primary |
| Full Research Pipeline | ⚪ | ⚪ | ✅ Primary |
| LLM Integration Cases | ⚪ | ✅ | ✅ Primary |
| End-to-End Scenarios | ⚪ | ⚪ | ✅ Primary |

**Real Simulation Notebook Example:**

```python
# tests/simulations/research_pipeline_simulation.ipynb

# ═══════════════════════════════════════════════════════════════
# SIMULATION: Full Research Pipeline - Nickel Market Analysis
# ═══════════════════════════════════════════════════════════════

# Cell 1: Setup Environment
from kea.services.orchestrator import Orchestrator
from kea.mcp_servers import ScraperServer, PythonServer, SearchServer
from kea.shared.logging import setup_simulation_logging

setup_simulation_logging(level="DEBUG")
print("✅ Environment Ready")

# Cell 2: Initialize MCP Servers (Real Instances)
scraper = ScraperServer.start()
python_exec = PythonServer.start()
search = SearchServer.start()

orchestrator = Orchestrator(
    mcp_servers=[scraper, python_exec, search]
)
print(f"✅ {len(orchestrator.tools)} tools registered")

# Cell 3: Execute Real Research Query
result = await orchestrator.research(
    query="Analyze nickel mining trends in Indonesia 2024",
    depth=2,
    max_sources=5
)

# Cell 4: Inspect Intermediate States (Observable)
print("📊 Research Stages:")
for stage in result.execution_log:
    print(f"  {stage.name}: {stage.duration_ms}ms - {stage.status}")

# Cell 5: Validate Output Artifacts
assert result.report is not None, "Report should be generated"
assert len(result.sources) >= 3, "Should have at least 3 sources"
assert result.data_artifacts, "Should have data artifacts"

# Display actual outputs
display(result.report[:500])  # Show report preview
display(result.sources)       # Show sources table

# Cell 6: Test Shadow Lab (Recalculation)
recalc_result = await orchestrator.shadow_lab(
    artifact_id=result.data_artifacts[0],
    instruction="Recalculate with 15% growth assumption"
)
print(f"✅ Recalculation completed: {recalc_result.summary}")

# Cell 7: Cleanup & Summary
await orchestrator.shutdown()
print("═" * 50)
print("SIMULATION COMPLETE")
print(f"  Total Duration: {result.total_duration_ms}ms")
print(f"  Tools Invoked: {result.tool_invocations}")
print(f"  Artifacts Generated: {len(result.data_artifacts)}")
```

**Case Categories:**

| Category | Example Cases |
|:---------|:--------------|
| **Happy Path** | Complete research flow, successful scraping, valid analysis |
| **Error Recovery** | Scraper timeout → retry, LLM rate limit → fallback |
| **Edge Cases** | Empty search results, malformed HTML, conflicting sources |
| **Performance** | Parallel 10-URL scrape, large DataFrame processing |
| **Integration** | MCP → Orchestrator → RAG → API Gateway flow |

**Hybrid Mode (Local + Cloud):**
- **Local:** Quick component simulations during development
- **Colab:** Validate individual MCP server behavior with real calls
- **Kaggle:** Full end-to-end research simulations with GPU acceleration

---

### Phase 8: Deployment *(Week 8-9)*
**Goal:** Production-ready deployment with full observability.

| Task | Description | Priority |
|:-----|:------------|:--------:|
| Create Dockerfiles | Multi-stage builds for all services + MCP servers | 🔴 Critical |
| Setup docker-compose | Local full-stack development | 🔴 Critical |
| **docker-compose.mcp.yml** | MCP servers standalone deployment | 🔴 Critical |
| Create Kubernetes manifests | Production cluster deployment | 🟡 High |
| **Deploy logging stack** | Loki + Promtail + Grafana | 🟡 High |
| **Setup tracing** | Jaeger/Zipkin for distributed tracing | 🟡 High |
| Setup monitoring | Prometheus + Grafana dashboards | 🟢 Medium |
| Security hardening | Secret management, network policies | 🟢 Medium |
| **MCP scaling** | Horizontal scaling for MCP servers | 🟢 Medium |

**Deliverables:**
- [ ] Docker images for all services and MCP servers
- [ ] docker-compose for local development
- [ ] **docker-compose.mcp.yml for isolated MCP testing**
- [ ] Kubernetes manifests for production
- [ ] **Logging stack deployment (Loki/Grafana)**
- [ ] **Distributed tracing deployment**
- [ ] Monitoring and alerting setup

---

## 🎯 Milestone Summary

| Milestone | Target | Key Deliverable |
|:----------|:-------|:----------------|
| **M0** | Week 1 | Project scaffolding & abstractions |
| **M1** | Week 2 | **Logging infrastructure & observability** |
| **M2** | Week 3 | **5 MCP Tool Servers operational** |
| **M3** | Week 4 | Orchestrator with MCP Client & parallel execution |
| **M4** | Week 5 | Memory vault with atomic facts |
| **M5** | Week 6 | Full API gateway with MCP management |
| **M6** | Week 7 | Async job processing with checkpoints |
| **M7** | Week 8 | >80% test coverage, CI/CD |
| **M8** | Week 9+ | Production deployment with full observability |

---

## 📊 Logging Standard

All services follow a unified structured logging format:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        LOGGING ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                │
│  │ Orchestrator│   │ MCP Servers │   │ API Gateway │                │
│  │  (service)  │   │  (tools)    │   │  (routes)   │                │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘                │
│         │                 │                 │                        │
│         └────────────┬────┴─────────────────┘                        │
│                      │                                               │
│           ┌──────────▼──────────┐                                    │
│           │  Structured Logger  │                                    │
│           │   (JSON Format)     │                                    │
│           │                     │                                    │
│           │ • trace_id          │                                    │
│           │ • span_id           │                                    │
│           │ • request_id        │                                    │
│           │ • service           │                                    │
│           │ • mcp_server        │                                    │
│           │ • tool_name         │                                    │
│           └──────────┬──────────┘                                    │
│                      │                                               │
│    ┌─────────────────┼─────────────────┐                             │
│    │                 │                 │                             │
│    ▼                 ▼                 ▼                             │
│ ┌──────┐       ┌──────────┐     ┌──────────┐                        │
│ │ File │       │ Promtail │     │ Console  │                        │
│ │ Logs │       │ (→ Loki) │     │ (Dev)    │                        │
│ └──────┘       └────┬─────┘     └──────────┘                        │
│                     │                                                │
│                     ▼                                                │
│              ┌──────────┐                                            │
│              │  Grafana │                                            │
│              │Dashboard │                                            │
│              └──────────┘                                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---
---

# 📐 Architecture Documentation

> This section documents the complete system architecture for Kea.

**Kea** is a microservice-based, recursive AI architecture designed for open-ended domain investigation. Unlike linear RAG systems, Kea utilizes a **Cyclic State Graph** to mimic human research behavior: formulating hypotheses, gathering data, verifying consistency, and autonomously reformulating strategies when results are suboptimal.

It separates **Reasoning** (The Brain/LLM) from **Execution** (The Muscle/Python), ensuring mathematical precision and hallucination-proof results.

---

## 🗺️ 1. The General Architecture (High-Level Map)

The system follows a **Hub-and-Spoke Microservices Pattern**. The central Orchestrator manages the lifecycle of a request, delegating work to specialized, isolated services via gRPC/REST.

```mermaid
graph TD
    %% --- STYLES ---
    classDef brain fill:#2d3436,stroke:#fff,stroke-width:2px,color:#fff;
    classDef router fill:#0984e3,stroke:#fff,stroke-width:2px,color:#fff;
    classDef memory fill:#6c5ce7,stroke:#fff,stroke-width:2px,color:#fff;
    classDef tool fill:#00b894,stroke:#333,stroke-width:2px,color:#fff;

    %% --- ACTORS ---
    User(("User / API")) -->|Query| Gateway["API Gateway & Rate Limiter"]
    Gateway --> Router{"Intention Router"}

    %% --- THE ROUTING LAYER ---
    Router --"Simple Q"--> FastRAG["⚡ Fast RAG / Memory"]
    Router --"Methodology Q"--> Provenance["🔍 Provenance Graph"]
    Router --"Recalculation"--> ShadowLab["🧮 Shadow Lab (Sandbox)"]
    Router --"Deep Research"--> Orchestrator["🧠 Main Orchestrator"]

    %% --- THE DEEP RESEARCH LOOP ---
    subgraph CognitiveCore ["The Cognitive Core"]
        Orchestrator --> Planner["📝 Planner & Decomposer"]
        Planner --> Keeper["🛡️ The Keeper (Context Guard)"]
        Keeper --> Divergence["✨ Divergence Engine (Analysis)"]
        Divergence --> Synthesizer["✍️ Report Synthesizer"]
    end

    %% --- THE TOOLS LAYER (The Muscle) ---
    subgraph Tools ["Tool Microservices"]
        Scraper["🕷️ Robotic Scraper"]:::tool
        Analyst["🐍 Python Analyst"]:::tool
        Meta["📊 Meta-Analysis"]:::tool
    end

    %% --- THE MEMORY LAYER (The Vault) ---
    subgraph MemoryVault ["The Triple-Vault Memory"]
        Atomic["Atomic Facts DB"]:::memory
        Episodic["Episodic Logs"]:::memory
        Artifacts["Parquet/Blob Store"]:::memory
    end

    %% --- CONNECTIONS ---
    Orchestrator <--> Scraper
    Orchestrator <--> Analyst
    Divergence <--> Atomic
    Scraper --> Artifacts
    Analyst --> Artifacts
```

---

## 🚦 2. Pipeline Routing Logic

Kea does not treat every query the same. It uses an **Intention Router** to determine the most efficient execution path.

### Path A: The "Memory Fork" (Incremental Research)
*   **Trigger:** User asks a question partially covered by previous research.
*   **Logic:**
    1.  **Introspection:** The Planner decomposes the query into atomic facts ($A, B, C$).
    2.  **Vector Lookup:** Checks `Atomic Facts DB` for $A, B, C$.
    3.  **Gap Analysis:**
        *   Found $A$ (Confidence > 0.9).
        *   Missing $B, C$.
    4.  **Delta Plan:** The system generates a research task *only* for $B$ and $C$, ignoring $A$.
*   **Outcome:** 50-80% reduction in API costs and latency.

### Path B: The "Shadow Lab" (Re-Calculation)
*   **Trigger:** User asks to modify a parameter of a previous result (e.g., "What if growth is 10% instead of 5%?").
*   **Logic:**
    1.  **Artifact Retrieval:** The system retrieves the clean `data.parquet` file from the `Artifacts Store` (S3/HuggingFace).
    2.  **Code Injection:** The system sends the data + the new parameter to the **Python Sandbox**.
    3.  **Execution:** Python recalculates the specific formula.
*   **Outcome:** Instant answer with zero new web scraping.

### Path C: The "Grand Synthesis" (Meta-Analysis)
*   **Trigger:** User asks to combine multiple research jobs (e.g., "Combine the Market Study and the Regulatory Study").
*   **Logic:**
    1.  **Librarian Fetch:** Retrieves `Job_ID_1` and `Job_ID_2` from the Manifest.
    2.  **Schema Alignment:** The **Analyst Agent** writes Python code to normalize columns (e.g., mapping `revenue_usd` to `rev_global`).
    3.  **Fusion:** Executes a `pd.concat` or merge operation.
    4.  **Conflict Check:** The **Divergence Engine** highlights where Job 1 contradicts Job 2.

```mermaid
graph TD
    %% --- STYLES ---
    classDef trigger fill:#2d3436,stroke:#fff,stroke-width:2px,color:#fff;
    classDef decision fill:#0984e3,stroke:#fff,stroke-width:2px,color:#fff;
    classDef action fill:#00b894,stroke:#333,stroke-width:2px,color:#fff;
    classDef output fill:#6c5ce7,stroke:#fff,stroke-width:2px,color:#fff;

    %% --- MAIN FLOW ---
    User(("User Input")):::trigger --> Router{"Intention Classifier<br/>(LLM Router)"}:::decision

    %% --- PATH A: THE MEMORY FORK (Incremental) ---
    subgraph PathA ["Path A: Incremental Research"]
        Router --"Follow-up / Update"--> VectorCheck["🔍 Check Atomic Facts DB"]
        VectorCheck --"Data Found"--> CacheHit["✅ Retrieve from Memory"]
        VectorCheck --"Data Missing"--> GapDetector{"Gap Analysis"}
        GapDetector -->|Only Search Missing| DeltaPlan["📉 Delta Planner"]
    end

    %% --- PATH B: THE SHADOW LAB (Recalculation) ---
    subgraph PathB ["Path B: Shadow Lab"]
        Router --"Recalculate / Modify"--> Loader["📂 Load .parquet Artifact"]
        Loader --> Sandbox["🐍 Python Sandbox<br/>(Execute New Formula)"]
    end

    %% --- PATH C: THE GRAND SYNTHESIS (Meta-Analysis) ---
    subgraph PathC ["Path C: Grand Synthesis"]
        Router --"Compare / Combine"--> Librarian["📚 Librarian<br/>(Fetch Job Manifests)"]
        Librarian --> Alchemist["⚗️ The Alchemist<br/>(Schema Alignment & Merge)"]
    end

    %% --- PATH D: DEEP RESEARCH (Fallback) ---
    subgraph PathD ["Path D: Zero-Shot Research"]
        Router --"New Topic"--> Planner["🧠 Full OODA Loop Planner"]
    end

    %% --- CONVERGENCE ---
    CacheHit --> Synthesizer
    DeltaPlan --> Scraper["🕷️ Robotic Scraper"]
    Scraper --> Synthesizer
    Sandbox --> Synthesizer
    Alchemist --> Synthesizer["✍️ Final Synthesis"]:::output
    Planner --> Scraper

```

---

## 🧬 3. Sub-Architectures (The "How-To")

### A. The "Keeper" Protocol (Context Immune System)
*Goal: To prevent the "Rabbit Hole" effect and hallucinations.*

```mermaid
sequenceDiagram
    participant Scraper as Robotic Scraper
    participant Quarantine as Quarantine Zone
    participant Keeper as The Keeper
    participant Brain as Orchestrator

    Scraper->>Quarantine: Ingest Raw Text (Chunked)
    loop Every Chunk
        Quarantine->>Keeper: Send Vector(Chunk)
        Keeper->>Keeper: Calc Cosine Similarity(User_Intent, Chunk)
        alt Similarity < 0.75 (Drift Detected)
            Keeper-->>Quarantine: 🔥 INCINERATE (Ignore)
        else Similarity > 0.75
            Keeper->>Brain: Release to Context
        end
    end
```

### B. The "Divergence Engine" (Abductive Reasoning)
*Goal: To investigate why data doesn't match expectations.*

```mermaid
graph LR
    Hypothesis(Expected: Revenue UP) --Collision--> Reality(Observed: Revenue DOWN)
    Reality --> Trigger{Divergence Type?}
    
    Trigger --"Numbers Wrong?"--> AgentA[Data Scientist: Normalize Units]
    Trigger --"Missing Factor?"--> AgentB[News Scout: Find Disruptions]
    Trigger --"Bias?"--> AgentC[Judge: Check Source Credibility]
    
    AgentA --> Synthesis
    AgentB --> Synthesis
    AgentC --> Synthesis
    Synthesis --> FinalReport[Explained Contradiction]
```

---

## 🛠️ Technology Stack

| Component | Tech | Role |
| :--- | :--- | :--- |
| **Orchestrator** | **Python / LangGraph** | Cyclic state management and consensus loops. |
| **API Interface** | **FastAPI** | Asynchronous microservice communication. |
| **Analysis** | **Pandas / DuckDB** | In-memory SQL/Dataframe manipulation for "Shadow Lab". |
| **Memory** | **Qdrant + GraphRAG** | Storage of atomic facts and their relationships. |
| **Storage** | **Parquet / S3** | Efficient storage of "Artifacts" (Raw DataFrames). |
| **Isolation** | **Docker / E2B** | Sandboxed code execution environment. |
| **Browser** | **Playwright** | Headless, stealthy web scraping with vision capabilities. |

---

## 🧠 4. The Cognitive Core & Workflow Logic

Kea differs from standard agents by implementing a **"Meta-Cognitive" Layer**. It does not simply execute a prompt; it *designs* the prompt required to execute the task, then critiques the result.

### 4.1. The "Meta-Prompt" Layer (System Prompt Definer)

To optimize for **cost** and **accuracy**, Kea uses a hierarchical model strategy. A cheaper "Architect Model" defines the persona for the "Worker Model."

**The Logic:**
1.  **Task Analysis:** The Planner receives a sub-task (e.g., "Extract financial ratios for Adaro 2024").
2.  **Persona Injection:** The Architect generates a specific System Prompt.
    *   *Input:* "Task: Finance extraction. Domain: Mining."
    *   *Generated Prompt:* "You are a Forensic Accountant. You ignore marketing fluff. You only output JSON. You prioritize tables over text."
3.  **Execution:** The Worker Model runs with this strict persona, reducing hallucinations.

```mermaid
sequenceDiagram
    participant Planner as 📝 Planner
    participant Architect as 🏗️ Architect (Small LLM)
    participant Worker as 👷 Worker (Large LLM)
    participant Tool as 🛠️ Python Tool

    Planner->>Architect: Send Task Context
    Note over Architect: Generates strict <br/>System Prompt
    Architect->>Worker: Inject Dynamic Persona
    Worker->>Tool: Execute Code/Search
    Tool-->>Worker: Return Raw Data
    Worker-->>Planner: Return Structured Result
```

---

### 4.2. The Consensus Engine (Adversarial Collaboration)

To prevent the "Yes-Man" problem (where AI blindly agrees with the first search result), Kea implements an **Adversarial Feedback Loop**. This simulates a boardroom meeting between three distinct personas.

**The Roles:**
1.  **The Generator (Optimist):** Gathers data and proposes an answer.
2.  **The Critic (Pessimist):** Scans the answer for logical fallacies, missing dates, or weak sources.
3.  **The Judge (Synthesizer):** Decides if the answer is "Market Ready" or needs "Revision."

**The Workflow:**

```mermaid
graph TD
    %% STYLES
    classDef role fill:#fff,stroke:#333,stroke-width:2px;
    classDef decision fill:#0984e3,stroke:#fff,stroke-width:2px,color:#fff;

    Start((Start)) --> Generator["🤠 Generator (Gather Data)"]:::role
    Generator --> Output["Draft Report"]
    Output --> Critic["🧐 Critic (Audit & Attack)"]:::role
    
    Critic --> Review{Pass Audit?}:::decision
    
    Review --"No (Flaws Found)"--> Feedback["📝 Correction Instructions"]
    Feedback --> Generator
    
    Review --"Yes (Verified)"--> Judge["⚖️ Judge (Final Polish)"]:::role
    Judge --> Final((Final Output))
```

---

### 4.3. The OODA Loop (Recursive Planning)

Kea operates on the military **OODA Loop** (Observe, Orient, Decide, Act) to handle "Unknown Unknowns." The plan is not static; it evolves as data is discovered.

*   **Observe:** The system ingests raw data from the web.
*   **Orient:** The **Keeper** compares this data against the user's intent vector.
*   **Decide:** The **Divergence Engine** determines if the hypothesis holds.
    *   *If Hypothesis Fails:* The system triggers a **"Pivot"**.
*   **Act:** The system spawns new sub-agents based on the *new* hypothesis.

**Example Scenario:**
1.  *Hypothesis:* "Nickel prices are up, so Mine Revenue should be up."
2.  *Observation:* "Mine Revenue is down."
3.  *Orientation:* Divergence Detected.
4.  *Decision (Pivot):* "Investigate 'Production Volume' and 'Weather Events'."
5.  *Act:* Spawn `Weather_Agent` and `Production_Agent`.

```mermaid
graph TD
    %% --- STYLES ---
    classDef observe fill:#fab1a0,stroke:#333,stroke-width:2px,color:#333;
    classDef orient fill:#74b9ff,stroke:#333,stroke-width:2px,color:#fff;
    classDef decide fill:#a29bfe,stroke:#333,stroke-width:2px,color:#fff;
    classDef act fill:#00b894,stroke:#333,stroke-width:2px,color:#fff;
    classDef fail fill:#ff7675,stroke:#333,stroke-width:2px,color:#fff;

    %% --- 1. OBSERVE (The Senses) ---
    subgraph Phase1 ["Phase 1: OBSERVE (Execution)"]
        Planner("📝 Current Plan"):::act --> Trigger("🚀 Trigger Agents"):::act
        Trigger --> Scraper("🕷️ Robotic Scraper"):::observe
        Scraper --> RawData["📄 Raw Ingested Data"]:::observe
    end

    %% --- 2. ORIENT (The Context) ---
    subgraph Phase2 ["Phase 2: ORIENT (Context Check)"]
        RawData --> Keeper{"🛡️ The Keeper"}:::orient
        Keeper --"Drift Detected<br/>(Irrelevant)"--> Incinerator("🔥 Prune Branch"):::fail
        Keeper --"Context Valid"--> ContextData["✅ Contextualized Facts"]:::orient
    end

    %% --- 3. DECIDE (The Hypothesis) ---
    subgraph Phase3 ["Phase 3: DECIDE (Divergence Check)"]
        ContextData --> Divergence{"✨ Divergence Engine"}:::decide
        Divergence --"Hypothesis Confirmed"--> Success["🏁 Validated Fact"]:::decide
        Divergence --"Hypothesis FAILED"--> Collision("💥 Collision Detected"):::decide
    end

    %% --- 4. ACT (The Pivot) ---
    subgraph Phase4 ["Phase 4: ACT (Recursive Pivot)"]
        Collision --> Abductive{"🕵️ Why did it fail?"}:::act
        
        Abductive --"Missing Factor?"--> NewFactor["➕ Add Variable: Weather/Strike"]:::act
        Abductive --"Bad Data?"--> NewSource["🔄 Switch Source: Gov vs News"]:::act
        
        NewFactor --> RePlan("🔄 Reformulate Plan"):::act
        NewSource --> RePlan
    end

    %% --- THE LOOP ---
    RePlan -.->|Recursive Loop| Planner
    Success --> Synthesizer("✍️ Final Synthesis")

```
---

## 💾 5. Memory & Data Structures

To support **"Jarvis-like" Recall** and **Meta-Analysis**, Kea utilizes specific data schemas. We do not just store text; we store **Structured Artifacts**.

### 5.1. The "Atomic Fact" Schema (Vector DB)
Used for **Incremental Research** (The "Memory Fork"). This allows the system to recall specific numbers without reading full reports.

```json
{
  "fact_id": "uuid_v4",
  "entity": "Adaro Energy",
  "attribute": "Revenue",
  "value": "6.5 Billion",
  "unit": "USD",
  "period": "FY2024",
  "source_url": "https://adaro.com/report.pdf",
  "confidence_score": 0.98,
  "vector_embedding": [0.12, -0.88, 0.45, ...]
}
```
```mermaid
graph LR
    %% --- STYLES ---
    classDef raw fill:#dfe6e9,stroke:#333,stroke-width:2px,color:#333;
    classDef process fill:#0984e3,stroke:#fff,stroke-width:2px,color:#fff;
    classDef schema fill:#00b894,stroke:#333,stroke-width:2px,color:#fff;
    classDef db fill:#6c5ce7,stroke:#fff,stroke-width:2px,color:#fff;

    %% --- INGESTION ---
    RawDoc["📄 Raw Document<br/>(PDF / HTML)"]:::raw --> Atomizer["⚛️ The Atomizer Agent<br/>(LLM Extractor)"]:::process

    %% --- THE SCHEMA TRANSFORMATION ---
    Atomizer --> FactJSON["🧩 Atomic Fact (JSON)"]:::schema
    
    subgraph SchemaDetail ["The Schema Structure"]
        FactJSON --"Entity: Adaro"--> F1["Entity"]
        FactJSON --"Attr: Revenue"--> F2["Attribute"]
        FactJSON --"Value: $6B"--> F3["Value"]
        FactJSON --"Time: 2024"--> F4["Period"]
    end

    %% --- STORAGE ---
    FactJSON --> Embedder["🧮 Embedding Model<br/>(Bi-Encoder)"]:::process
    Embedder --> VectorDB[("💠 Vector DB<br/>(Qdrant/Weaviate)")]:::db

    %% --- RETRIEVAL FLOW ---
    subgraph Recall ["Incremental Retrieval"]
        Query("User Query: Adaro Revenue") --> Search["🔍 Similarity Search"]:::process
        VectorDB <--> Search
        Search --"Match > 0.9"--> Hit["✅ Cache Hit"]:::schema
        Search --"No Match"--> Miss["❌ Gap Detected"]:::raw
    end
```

### 5.2. The "Conversation Project" Schema (JSON)
Used for **Grand Synthesis** and **Systematic Reviews**. This tracks the *provenance* of every job in a session.

```json
{
  "session_id": "sess_99",
  "topic": "Nickel Market Analysis",
  "jobs": [
    {
      "job_id": "job_01",
      "type": "market_research",
      "status": "completed",
      "artifacts": {
        "raw_data": "s3://bucket/sess_99/job_01_data.parquet",
        "report": "s3://bucket/sess_99/job_01_report.md",
        "code_snippets": ["s3://.../calc_cagr.py"]
      }
    },
    {
      "job_id": "job_02",
      "type": "regulatory_check",
      "status": "completed",
      "artifacts": {
        "raw_data": "s3://bucket/sess_99/job_02_data.parquet"
      }
    }
  ]
}
```
```mermaid
graph TD
    %% --- STYLES ---
    classDef root fill:#2d3436,stroke:#fff,stroke-width:2px,color:#fff;
    classDef job fill:#0984e3,stroke:#fff,stroke-width:2px,color:#fff;
    classDef artifact fill:#00b894,stroke:#333,stroke-width:2px,color:#fff;
    classDef storage fill:#fdcb6e,stroke:#333,stroke-width:2px,color:#333;

    %% --- THE ROOT SESSION ---
    Session["📁 Session Object (JSON)<br/>ID: sess_99"]:::root --> Topic["Topic: Nickel Market Analysis"]:::root
    Session --> JobList["Jobs Array"]:::root

    %% --- JOB 1: MARKET RESEARCH ---
    subgraph Job1 ["Job 01: Market Research"]
        JobList --> J1["Job ID: job_01<br/>Status: Completed"]:::job
        J1 --"Pointer"--> Art1["Artifacts Manifest"]:::artifact
        
        Art1 -.->|Path| S3_Data1[("☁️ S3: job_01_data.parquet<br/>(Raw Financials)")]:::storage
        Art1 -.->|Path| S3_Rep1[("☁️ S3: job_01_report.md<br/>(Text Summary)")]:::storage
        Art1 -.->|Path| Py_Code1[("☁️ S3: calc_cagr.py<br/>(Reproducible Code)")]:::storage
    end

    %% --- JOB 2: REGULATORY CHECK ---
    subgraph Job2 ["Job 02: Regulatory Check"]
        JobList --> J2["Job ID: job_02<br/>Status: Completed"]:::job
        J2 --"Pointer"--> Art2["Artifacts Manifest"]:::artifact
        
        Art2 -.->|Path| S3_Data2[("☁️ S3: job_02_laws.parquet<br/>(Legal Clauses)")]:::storage
    end

    %% --- THE CONSUMER ---
    Session --> Librarian{"📚 The Librarian"}:::root
    Librarian -->|Fetch All Parquet Files| Alchemist["⚗️ The Alchemist<br/>(Grand Synthesis)"]:::job
```
### 5.3. The "Shadow Lab" Workflow (Re-Calculation)
This architecture allows users to ask "What if?" questions without triggering new web searches.

1.  **User Request:** "Recalculate Job 1 assuming 10% inflation."
2.  **Loader:** Pulls `job_01_data.parquet` from S3.
3.  **Sandbox:** Loads Parquet into Pandas DataFrame.
4.  **Execution:** Runs `df['adjusted_revenue'] = df['revenue'] * 1.10`.
5.  **Output:** Returns table immediately. **Zero Web Requests.**

---
```mermaid
graph TD
    %% --- STYLES ---
    classDef input fill:#2d3436,stroke:#fff,stroke-width:2px,color:#fff;
    classDef storage fill:#fdcb6e,stroke:#333,stroke-width:2px,color:#333;
    classDef compute fill:#0984e3,stroke:#fff,stroke-width:2px,color:#fff;
    classDef sandbox fill:#00b894,stroke:#333,stroke-width:2px,color:#fff;

    %% --- TRIGGER ---
    User("User: 'Recalculate Job 1 with 10% inflation'"):::input --> Router{"Intention Router"}:::input
    
    %% --- THE SHADOW LAB ISOLATION ---
    subgraph ShadowLab ["🔬 The Shadow Lab (Offline)"]
        
        Router --"Modify Param"--> Coder["👨‍💻 Code Generator<br/>(LLM)"]:::compute
        
        %% --- DATA LOADING ---
        Router --"Fetch Data"--> Loader["📂 Artifact Loader"]:::storage
        S3[("☁️ S3 Artifact Store<br/>(job_01_data.parquet)")]:::storage -.->|Load DataFrame| Loader
        
        %% --- EXECUTION ---
        Coder --"1. Generate Script"--> Sandbox["🐍 Python Sandbox<br/>(E2B / Docker)"]:::sandbox
        Loader --"2. Inject DataFrame"--> Sandbox
        
        Sandbox --"3. Execute"--> Result["📊 New Calculation Result"]:::sandbox
    end

    %% --- OUTPUT ---
    Result --> Output("Response: 'Adjusted Revenue is $7.1B'"):::input
    
    %% --- BYPASS VISUALIZATION ---
    Internet((Internet / Web))
    Router -.->|⛔ BYPASS| Internet
```

## 🤖 6. The Robotic Infrastructure (The "Hands")

To function as a true Deep Research Engine, Kea must navigate the modern, hostile web. It uses a **Stealth Robotic Fleet** to handle scraping, avoiding bans, and reading complex UIs.

### 6.1. The Headless Browser Fleet
Instead of simple HTTP requests (which get blocked), Kea controls a cluster of headless browsers.

*   **Technology:** Playwright (Python) + `stealth` plugins.
*   **Rotation Logic:**
    *   **User-Agent Rotation:** Mimics different devices (iPhone, Mac, Windows) per request.
    *   **IP Rotation:** Routes traffic through residential proxies if a 403 Forbidden is detected.
*   **Visual Scraping Protocol:**
    *   If `HTML Parsing` fails (due to dynamic JS or obfuscation), the system triggers **Vision Mode**.
    *   **Snapshot:** Takes a screenshot of the viewport.
    *   **Vision Model:** Sends image to GPT-4o-Vision/Gemini-Pro-Vision with prompt: *"Extract the table data from this image into JSON."*

```mermaid
graph TD
    %% --- STYLES ---
    classDef control fill:#2d3436,stroke:#fff,stroke-width:2px,color:#fff;
    classDef infra fill:#0984e3,stroke:#fff,stroke-width:2px,color:#fff;
    classDef logic fill:#00b894,stroke:#333,stroke-width:2px,color:#fff;
    classDef external fill:#fdcb6e,stroke:#333,stroke-width:2px,color:#333;

    %% --- INPUT ---
    Queue[("URL Queue")] --> FleetMgr{"Fleet Manager"}:::control

    %% --- INFRASTRUCTURE CONFIG ---
    subgraph StealthConfig ["Stealth Configuration"]
        FleetMgr --"Assign IP"--> Proxy["Residential Proxy Pool"]:::infra
        FleetMgr --"Spoof Headers"--> UA["User-Agent Rotator<br/>(iPhone/Chrome/Mac)"]:::infra
        
        Proxy --> Browser
        UA --> Browser
    end

    %% --- THE BROWSER INSTANCE ---
    subgraph BrowserNode ["Headless Browser Instance"]
        Browser["🎭 Playwright Engine<br/>(Stealth Mode)"]:::logic
        Browser --"1. Load Page"--> PageContent["Page DOM / Canvas"]
        
        %% --- DECISION LOGIC ---
        PageContent --> Check{Is Readable?}:::control
        
        %% --- PATH A: STANDARD PARSING ---
        Check --"Yes (Text/HTML)"--> Parser["📄 HTML Parser<br/>(BeautifulSoup)"]:::logic
        
        %% --- PATH B: VISION MODE (The Backup) ---
        Check --"No (Obfuscated/Chart)"--> Screenshot["📸 Take Snapshot"]:::logic
        Screenshot --> VisionLLM["👁️ Vision Model<br/>(GPT-4o / Gemini)"]:::external
        
        %% --- OUTPUT ---
        Parser --> CleanData["✅ Clean JSON"]
        VisionLLM --"OCR / Interpret"--> CleanData
    end
```

### 6.2. Politeness & Rate Limiting
To ensure long-term stability and ethical scraping, Kea implements **Domain-Level Throttling**.

```mermaid
graph LR
    Job[Scrape Job] --> Limiter{Check Limits}
    
    Limiter --"google.com (100 req/min)"--> BucketA[High Capacity Bucket]
    Limiter --"idx.co.id (5 req/min)"--> BucketB[Low Capacity Bucket]
    
    BucketA --> Execute
    BucketB --"Wait 10s"--> Execute
```

---

## ⏳ 7. Asynchronous Task Management

Deep research takes time (minutes to hours). A standard HTTP request will timeout. Kea uses an **Event-Driven Architecture**.

### 7.1. The "Fire-and-Forget" Pattern
1.  **Client:** POST `/api/research/start`
2.  **API:** Returns `202 Accepted` + `job_id`.
3.  **Queue:** Pushes job to **Redis**.
4.  **Worker:** Picks up job, runs for 45 minutes, updates **PostgreSQL** state.
5.  **Client:** Polls `/api/research/status/{job_id}` or receives Webhook.

```mermaid
graph LR
    %% --- STYLES ---
    classDef client fill:#ff7675,stroke:#333,stroke-width:2px,color:#fff;
    classDef api fill:#0984e3,stroke:#fff,stroke-width:2px,color:#fff;
    classDef queue fill:#fdcb6e,stroke:#333,stroke-width:2px,color:#333;
    classDef worker fill:#00b894,stroke:#333,stroke-width:2px,color:#fff;
    classDef db fill:#6c5ce7,stroke:#fff,stroke-width:2px,color:#fff;

    %% --- ACTORS ---
    User(("User / Frontend")):::client
    
    subgraph SynchronousLayer ["⚡ Synchronous Layer (Fast)"]
        API["API Gateway<br/>(FastAPI)"]:::api
        Redis[("Redis Task Queue")]:::queue
    end

    subgraph AsyncLayer ["🐢 Asynchronous Layer (Deep Work)"]
        Worker["👷 Background Worker<br/>(Orchestrator Instance)"]:::worker
        Postgres[("PostgreSQL<br/>Job State & History")]:::db
    end

    %% --- STEP 1: THE TRIGGER (FIRE) ---
    User --"1. POST /research/start"--> API
    API --"2. Push Job Payload"--> Redis
    API --"3. Return HTTP 202 Accepted<br/>(Contains: job_id)"--> User

    %% --- STEP 2: THE EXECUTION (FORGET) ---
    Redis -.->|"4. Worker Pops Job"| Worker
    Worker -->|"5. Run Deep Research Loop<br/>(Takes 10-60 mins)"| Worker
    Worker --"6. Update Status: COMPLETED"--> Postgres

    %% --- STEP 3: THE CHECKUP ---
    User -.->|"7. Poll GET /status/{job_id}"| API
    API --"8. Query State"--> Postgres
```
### 7.2. Distributed State Machine
Since the process is long, the state must be persisted. We use **LangGraph Checkpointing**.
*   **Benefit:** If the server crashes at *Step 4 (Analysis)*, it restarts exactly at Step 4, not Step 1.
*   **Pause/Resume:** The system can pause to ask the user for confirmation ("I found a conflict, continue?") and resume days later.

```mermaid
graph TD
    %% --- STYLES ---
    classDef execute fill:#00b894,stroke:#333,stroke-width:2px,color:#fff;
    classDef save fill:#0984e3,stroke:#fff,stroke-width:2px,color:#fff;
    classDef db fill:#2d3436,stroke:#fff,stroke-width:2px,color:#fff;
    classDef crash fill:#d63031,stroke:#333,stroke-width:2px,color:#fff;
    classDef recover fill:#fdcb6e,stroke:#333,stroke-width:2px,color:#333;

    %% --- THE THREAD ---
    subgraph ExecutionFlow ["Active Research Thread (ID: 123)"]
        Step1["Step 1: Planner Node"]:::execute --> Save1{"💾 Checkpoint State"}:::save
        Save1 --> Step2["Step 2: Scraper Node"]:::execute
        Step2 --> Save2{"💾 Checkpoint State"}:::save
        
        Save2 --> Crash["🔥 SERVER CRASH / RESTART"]:::crash
    end

    %% --- THE PERSISTENCE LAYER ---
    subgraph StateStore ["PostgreSQL State Store"]
        Postgres[("🐘 DB Table: checkpoints<br/>Key: thread_id_123<br/>Blob: {plan: ..., data: ...}")]:::db
    end

    %% --- THE RECOVERY ---
    subgraph RecoveryFlow ["Recovery / Resume"]
        Restart("🚀 Worker Restart"):::recover --> Load("📂 Load Last Checkpoint<br/>(thread_id_123)"):::recover
        Load --> Resume("▶️ Resume at Step 3: Analysis<br/>(Skip Steps 1 & 2)"):::execute
    end

    %% --- CONNECTIONS ---
    Save1 -.->|Serialize & UPSERT| Postgres
    Save2 -.->|Serialize & UPSERT| Postgres
    Postgres -.->|Deserialize| Load
    Crash -.-> Restart
```

---

## 🚢 8. Deployment Strategy

Kea is designed to be **Infrastructure Agnostic**. It runs on a laptop (Colab/Docker) or a cluster (Kubernetes) using the same code base, controlled by Environment Variables.

### 8.1. The Config Switch
We use a centralized configuration loader that detects the environment.

| Feature | Local / Colab Mode | Production / VPS Mode |
| :--- | :--- | :--- |
| **Database** | SQLite (File) | PostgreSQL (Server) |
| **Queue** | Python `threading` | Redis |
| **Vector DB** | Chroma (Local File) | Qdrant / Weaviate (Server) |
| **Browser** | Local Playwright | Browserless / ScrapingBee |

### 8.2. Production Docker Compose
The system is deployed as a mesh of services.

```yaml
version: '3.8'
services:
  # The Brain
  orchestrator:
    image: kea/orchestrator
    environment:
      - MODE=production
    depends_on: [redis, db]
  
  # The Hands (Isolated for security)
  tool-runner:
    image: kea/sandbox
    command: python -m tools.server
    
  # The State
  redis: {image: "redis:alpine"}
  db: {image: "postgres:15"}
  qdrant: {image: "qdrant/qdrant"}
```

---

## 🔌 9. API Interface (The User Layer)

The API follows a **Polymorphic Asynchronous Pattern**. It is designed to be "infrastructure agnostic," meaning the same API structure works whether the backend is a simple Python script or a Kubernetes cluster.

### 9.1. Base Configuration

*   **Base URL:** `/api/v1`
*   **Versioning:** Strict URI versioning (`v1`, `v2`) to allow breaking changes without disrupting existing connectors.
*   **Authentication:** Bearer Token (JWT).
*   **Content-Type:** `application/json`

---

### 9.2. The Universal "Job" Endpoint (The Core Lego)

Instead of hardcoding `/research` or `/scrape` endpoints, we use a single **Job Dispatcher**. This allows you to add new "Agent Types" (e.g., a Video Analyzer) in the backend without changing the frontend API client.

### A. Submit a Job
**Endpoint:** `POST /jobs`

**Request Payload:**
```json
{
  "project_id": "session_alpha_99",  // Links to a specific conversation/memory context
  "type": "deep_research",           // <--- THIS IS THE SWITCH (research, synthesis, shadow_lab)
  "priority": "normal",              // high, normal, background
  "callback_url": "https://myapp.com/webhook", // Optional: For async notification
  
  // The "Lego" Config - Schema validation changes based on 'type'
  "payload": {
    "query": "Future of Nickel Mining in Sulawesi",
    "depth": 3,
    "constraints": {
      "time_range": ["2023-01-01", "2025-12-31"],
      "domains": ["reuters.com", "esdm.go.id"],
      "excluded_domains": ["reddit.com"]
    }
  }
}
```

**Response (Immediate 202 Accepted):**
```json
{
  "job_id": "job_550e8400-e29b",
  "status": "queued",
  "queue_position": 4,
  "tracking_url": "/api/v1/jobs/job_550e8400-e29b",
  "estimated_time_sec": 300
}
```

### B. Check Job Status / Poll Result
**Endpoint:** `GET /jobs/{job_id}`

**Response (While Running):**
```json
{
  "job_id": "job_550e8400-e29b",
  "status": "processing",
  "progress": 45, // Percent
  "current_stage": "analyzing_financials", // Granular step
  "logs": [
    {"ts": "10:00:01", "msg": "Scraping completed. Found 14 sources."},
    {"ts": "10:00:05", "msg": "Context drift detected in Source 4. Pruning."}
  ]
}
```

**Response (Completed):**
```json
{
  "job_id": "job_550e8400-e29b",
  "status": "completed",
  "result": {
    "summary": "Nickel prices are projected to...",
    "artifacts": {
      "report_markdown": "s3://.../report.md",
      "raw_data": "s3://.../data.parquet",
      "visuals": ["s3://.../chart1.png"]
    }
  },
  "usage": {"tokens": 4500, "search_calls": 12}
}
```

---

### 9.3. The "Lego" Payload Types

This is where the modularity happens. The `payload` object changes based on the `type`.

#### Type 1: `deep_research` (The Standard)
*   **Purpose:** Standard web scraping and reasoning.
*   **Payload Config:**
    ```json
    {
      "query": "...",
      "mode": "autonomous", // or "guided" (asks human for help)
      "output_format": "html"
    }
    ```

#### Type 2: `synthesis` (The Alchemist)
*   **Purpose:** Combining previous jobs.
*   **Payload Config:**
    ```json
    {
      "input_job_ids": ["job_123", "job_456"],
      "synthesis_mode": "meta_analysis", // or "systematic_review"
      "conflict_resolution": "highlight" // or "trust_latest"
    }
    ```

#### Type 3: `shadow_lab` (Re-Calculation)
*   **Purpose:** Running code on existing artifacts (No Internet).
*   **Payload Config:**
    ```json
    {
      "artifact_id": "job_123_data.parquet",
      "instruction": "Recalculate EBITDA column with 10% tax rate",
      "output_type": "json_table"
    }
    ```

---

### 9.4. The Memory & Knowledge API

Endpoints to inspect, modify, and "debug" the system's brain.

#### A. Semantic Search (Recall)
**Endpoint:** `POST /memory/search`
*   **Use Case:** "What do we *already* know about Adaro?"
*   **Payload:** `{"query": "Adaro revenue", "threshold": 0.8}`
*   **Response:** List of "Atomic Facts" with source pointers.

#### B. The Provenance Graph (Audit)
**Endpoint:** `GET /memory/provenance/{job_id}`
*   **Use Case:** Visualizing the research path in a frontend.
*   **Response:** Nodes and Edges JSON (compatible with ReactFlow/Cytoscape).

#### C. Blacklist Management (The Immune System)
**Endpoint:** `POST /config/blacklist`
*   **Use Case:** Manually blocking a bad source.
*   **Payload:** `{"domain": "fake-news.com", "reason": "Hallucination risk"}`

---

### 9.5. The "Human-in-the-Loop" API

Future-proofing for when the AI needs help.

#### A. List Active Interventions
**Endpoint:** `GET /interventions`
*   **Response:** List of jobs currently PAUSED waiting for human input.
    *   *Example:* "Job 555 paused. Reason: Keeper detected 80% ambiguity in query."

#### B. Submit Feedback
**Endpoint:** `POST /interventions/{id}/resolve`
*   **Payload:** `{"decision": "proceed", "feedback": "Focus only on thermal coal, not coking coal."}`

---

### 9.6. Connectors (System Capabilities)

This allows the frontend to dynamically render the "Tools" available, even as you add new ones (like Audio or Video).

**Endpoint:** `GET /system/capabilities`

**Response:**
```json
{
  "version": "1.2.0",
  "available_agents": [
    {"id": "scraper_v1", "name": "Web Scraper", "cost_per_run": "medium"},
    {"id": "analyst_v2", "name": "Python Sandbox", "cost_per_run": "low"},
    {"id": "vision_v1", "name": "Chart Reader", "cost_per_run": "high"} // New feature added
  ],
  "supported_file_types": ["parquet", "csv", "json", "pdf"]
}
```

---

### 9.7. API Architecture Diagram

```mermaid
graph LR
    %% --- STYLES ---
    classDef client fill:#ff7675,stroke:#333,stroke-width:2px,color:#fff;
    classDef router fill:#0984e3,stroke:#fff,stroke-width:2px,color:#fff;
    classDef handler fill:#00b894,stroke:#333,stroke-width:2px,color:#fff;

    %% --- ACTORS ---
    Client(("Frontend / SDK")):::client --> Gateway["API Gateway /v1"]:::router

    %% --- ROUTES ---
    subgraph Routes
        Gateway --"/jobs (POST)"--> Dispatcher{"Job Dispatcher"}:::router
        Gateway --"/jobs/{id} (GET)"--> StatusCheck["Status Monitor"]:::handler
        Gateway --"/memory/*"--> MemoryMgr["Memory Manager"]:::handler
        Gateway --"/system/*"--> SysConfig["System Config"]:::handler
    end

    %% --- DISPATCH LOGIC ---
    Dispatcher --"type: deep_research"--> AgentA["Research Agent"]:::handler
    Dispatcher --"type: synthesis"--> AgentB["Synthesis Agent"]:::handler
    Dispatcher --"type: shadow_lab"--> AgentC["Shadow Lab Agent"]:::handler

    %% --- FUTURE PROOFING ---
    Dispatcher -.->|"type: audio_analysis"| AgentNew["(Future) Audio Agent"]:::handler
```
### 9.8. API Endpoint Structure

#### **1. Job Dispatcher (The Core)**
*Handles Research, Synthesis, and Shadow Lab execution.*

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/jobs` | `POST` | Submit a new polymorphic job (Research, Synthesis, Calc). |
| `/api/v1/jobs` | `GET` | List all recent jobs with filtering/pagination. |
| `/api/v1/jobs/{id}` | `GET` | Get real-time status, logs, and progress of a job. |
| `/api/v1/jobs/{id}` | `DELETE` | Cancel/Terminate a running job immediately. |
| `/api/v1/jobs/{id}/retry` | `POST` | Re-run a failed job with the same configuration. |

#### **2. Memory & Knowledge Brain**
*Interacts with the Vector DB, Atomic Facts, and Graphs.*

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/memory/search` | `POST` | Perform semantic search against Atomic Facts DB. |
| `/api/v1/memory/graph/{job_id}` | `GET` | Retrieve the Provenance Graph (Nodes/Edges) for UI. |
| `/api/v1/memory/fact` | `POST` | Manually insert or correct a fact in memory. |
| `/api/v1/memory/fact/{id}` | `DELETE` | Delete/Invalidate a specific atomic fact. |
| `/api/v1/memory/project/{id}` | `GET` | Get the full Manifest (JSON) of a specific session. |

#### **3. Artifacts & Storage**
*Accessing heavy files generated by the system (Parquet, PDF, Charts).*

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/artifacts/{id}` | `GET` | Download a raw artifact file (binary stream). |
| `/api/v1/artifacts/{id}/preview` | `GET` | Get a lightweight preview (e.g., first 10 rows of Parquet). |
| `/api/v1/artifacts/upload` | `POST` | Upload user documents (PDF/CSV) to be analyzed. |

#### **4. Human-in-the-Loop (Interventions)**
*Managing pauses, confirmations, and feedback.*

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/interventions` | `GET` | List all jobs currently paused waiting for human input. |
| `/api/v1/interventions/{id}` | `GET` | Get details of the decision needed (e.g., choices). |
| `/api/v1/interventions/{id}/resolve`| `POST` | Submit human decision to resume the job. |

#### **5. System & Connectors**
*Configuration, Capabilities, and Health.*

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/system/capabilities` | `GET` | List active Agents/Tools (e.g., Scraper, Analyst, Vision). |
| `/api/v1/system/health` | `GET` | Check status of Microservices (Redis, DB, Scraper). |
| `/api/v1/system/config` | `PATCH` | Hot-swap global settings (e.g., Rate Limits). |
| `/api/v1/system/blacklist` | `POST` | Add a domain to the global exclusion list. |

#### **6. LLM Provider Management**
*Managing the AI models used by the Orchestrator.*

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/llm/providers` | `GET` | List available providers (OpenAI, Gemini, Anthropic). |
| `/api/v1/llm/models` | `GET` | List available models for a specific provider. |
| `/api/v1/llm/config` | `POST` | Update active model per Role (e.g., "Planner" = GPT-4o). |
| `/api/v1/llm/usage` | `GET` | Get token usage statistics and cost estimation. |
---

## 🛡️ 10. Roadmap & Future Proofing

### Phase 1: Foundation (Current)
*   [x] Microservice Architecture.
*   [x] Cyclic Research Graph (OODA Loop).
*   [x] Atomic Fact Memory.

### Phase 2: Perception (Next)
*   [ ] **Multimodal Input:** Allow users to upload a PDF/Image as the start of research.
*   [ ] **Audio Output:** Generate an "Executive Podcast" summary of the research.

### Phase 3: Collaboration (Long Term)
*   [ ] **Swarm Protocol:** Allow multiple "Kea" instances to talk to each other across different servers (e.g., a Finance Kea talking to a Legal Kea).
*   [ ] **Human-in-the-Loop UI:** A dashboard to visualize the "Thought Graph" and manually prune branches.

---

