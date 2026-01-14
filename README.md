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

> ⚠️ **IMPORTANT:** 
> - **"Kea"** = Project/Product name only (use in documentation, README, marketing)
> - **"DARE"** = Methodology term only (Distributed Autonomous Research Engine)
> - **Neither** should appear in code, classes, functions, variables, directories, or metrics

| Element | ❌ Avoid | ✅ Use |
|:--------|:---------|:-------|
| **Package name** | `kea`, `dare` | Generic name or no prefix |
| **Directories** | `kea/`, `dare_service/` | `services/`, `core/`, `shared/` |
| **Classes** | `KeaOrchestrator`, `DareClient` | `Orchestrator`, `MCPClient` |
| **Functions** | `kea_search()`, `run_dare()` | `search()`, `run_research()` |
| **Variables** | `kea_config`, `dare_result` | `config`, `research_result` |
| **Modules** | `kea_utils.py` | `utils.py`, `helpers.py` |
| **Metrics** | `kea_*`, `dare_*` | `research_*`, `tool_*` |

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

---

## 📋 Development Status

### ✅ v1.0 Complete
All foundation phases have been completed:

| Phase | Status | Key Deliverables |
|:------|:------:|:-----------------|
| **Phase 0-1** | ✅ | Project scaffolding, logging infrastructure |
| **Phase 2** | ✅ | 14 MCP tools across 5 servers |
| **Phase 3** | ✅ | Orchestrator with LangGraph, MCP Client |
| **Phase 4** | ✅ | RAG Service with vector store |
| **Phase 5** | ✅ | API Gateway with 8 route modules |
| **Phase 6** | ✅ | 3 background workers |
| **Phase 7** | ✅ | 79+ test files, pytest configuration |
| **Phase 8** | ✅ | Docker deployment, Prometheus/Grafana |

---

## 🚀 v2.0 Roadmap (NEXT)

### Vision
Transform Kea into a **systemic, self-adapting research automation engine** that operates like a corporation with 100K specialized employees.

### 🏗️ Core Architecture Principles

| Principle | Description |
|-----------|-------------|
| **Systemic AI** | Not single persona—self-multiplying agent swarm with dynamic system prompts |
| **ARM Modularity** | LangGraph core + optional MCP tool extensions (like ARM unified chips) |
| **JIT Dependencies** | `uv` on-demand package install (no 1000-package requirements.txt) |
| **Tool Isolation** | Each MCP server runs in own process (avoids dependency conflicts) |
| **Hardware Efficiency** | Must run on VPS KVM2 / Colab Free / Kaggle |
| **Text-First** | Multimodal via Gemini later, text focus now |
| **Self-Evolution** | Build own knowledge base, store learned parsers to HuggingFace |
| **Conversational** | Follow-up, not restart—detect intent (DEEPER/REVISE/NEW_TOPIC) |
| **Smart Context** | Inject relevant facts + pointers, not entire datasets |
| **Curiosity-Driven** | Proactive WHY questions, WHAT-IF scenarios, anomaly detection |

### v2.1: Core Orchestrator Hardening ✅ COMPLETE
- `shared/hardware/` - Resource monitor (RAM/CPU/GPU tracking)
- `services/orchestrator/core/degradation.py` - GracefulDegrader, throttling
- `services/orchestrator/core/recovery.py` - @retry, CircuitBreaker

### v2.2: JIT Dependencies + Tool Isolation ✅ COMPLETE
- `shared/tools/jit_loader.py` - `uv` integration for on-demand install
- `configs/tools.yaml` - Tool dependency manifest (30+ tools)
- `shared/tools/isolation.py` - Process isolation, LazyToolLoader

### v2.3: System Prompt Factory ✅ COMPLETE
- `services/orchestrator/core/prompt_factory.py`
- 7 domains (Finance/Medical/Legal/Engineering/Academic/Data/General)
- 8 task types (Research/Analysis/Summarize/Compare/Extract/Validate/Forecast/Explain)

### v2.4: Agent Spawner/Scaler ✅ COMPLETE
- `services/orchestrator/core/agent_spawner.py`
- TaskDecomposer with entity/aspect/comparison strategies
- Parallel agent execution with semaphore control

### v2.5: HuggingFace Persistence ✅ COMPLETE
- `shared/storage/hf_sync.py`
- Job checkpoints, parser storage, config backup

### v2.6: 1000+ Tool Routing ✅ COMPLETE
- `shared/mcp/tool_router.py`
- ToolIndex with 12 categories, semantic matching
- Lazy loading integration

### v2.7: Conversational Memory ✅ COMPLETE
- `services/orchestrator/core/conversation.py`
- 7 intents (FOLLOW_UP/DEEPER/REVISE/NEW_TOPIC/COMPARE/CLARIFY/CONFIRM)
- SmartContextBuilder with fact relevance scoring

### v2.8: Curiosity Engine ✅ COMPLETE
- `services/orchestrator/core/curiosity.py`
- WHY question generation (causal reasoning)
- WHAT-IF scenario simulation
- Anomaly detection across research facts

---

## 🔧 Model Configuration

```yaml
# configs/models.yaml
llm:
  primary:
    provider: "openrouter"
    model: "nvidia/nemotron-3-nano-30b-a3b:free"
    context_length: 256000  # 256K native
  backup:
    provider: "google"
    model: "gemini-3-flash-preview"
    
embedding:
  default: "Qwen/Qwen3-Embedding-0.6B"
  fallback: "qwen/qwen3-embedding-8b"
  
reranker:
  default: "Qwen/Qwen3-Reranker-0.6B"
```

```yaml
# configs/tools.yaml
jit_install: true
package_manager: "uv"

tool_deps:
  pdf_extract: ["pymupdf", "pdfplumber"]
  ml_train: ["scikit-learn", "xgboost"]
  web_scrape: ["playwright"]
```

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

### v1.0: Foundation ✅ Complete
*   [x] Microservice Architecture
*   [x] Cyclic Research Graph (OODA Loop)
*   [x] Atomic Fact Memory
*   [x] 14 MCP Tools, 8 API Routes, 3 Workers

### v2.0: Systemic AI Platform ✅ Complete
*   [x] **v2.1 Hardware Monitoring:** Resource detection, memory pressure tracking
*   [x] **v2.2 Graceful Degradation:** Auto-throttle under pressure, circuit breakers
*   [x] **v2.3 JIT Dependencies:** `uv` on-demand install, tool isolation
*   [x] **v2.4 System Prompt Factory:** Dynamic prompts per domain/task
*   [x] **v2.5 Agent Spawner:** Self-multiplying agents for massive tasks
*   [x] **v2.6 HuggingFace Sync:** Cross-session persistence
*   [x] **v2.7 Conversational Memory:** Intent detection, smart context injection
*   [x] **v2.8 Curiosity Engine:** Auto-generate follow-up questions

### v3.0: Enterprise Kernel ✅ Complete
*   [x] **Organization Module:** Department → Team → Agent hierarchy
*   [x] **Work Unit System:** WorkBoard, Priority, dependencies
*   [x] **Message Bus:** Inter-agent communication, request-response
*   [x] **Supervisor Layer:** QualityGate, escalation, health monitoring
*   [x] **Security Hardening:** ResourceGuard, KillSwitch, rate limiting

```
Organization
├── Department (domain-specialized)
│   ├── Team (coordinated agent pool)
│   │   └── AgentInstance (role-based)
│   └── WorkBoard (task management)
└── Supervisor (oversight + escalation)
```

### v3.1: Distributed Operations 🛠️ Planned
*   [ ] **Multi-Process Workers:** Process-based agent isolation
*   [ ] **Redis Message Broker:** Pub/sub for MessageBus
*   [ ] **Prometheus Metrics:** Full observability

### v4.0: Swarm Intelligence (Long Term)
*   [ ] **Multi-Kea Protocol:** Instances talk to each other (Finance ↔ Legal)
*   [ ] **Knowledge Synthesis:** Build evolving knowledge bases
*   [ ] **Kubernetes Orchestration:** Auto-scale agent pods
*   [ ] **Multimodal:** Gemini Flash for vision/audio

---
