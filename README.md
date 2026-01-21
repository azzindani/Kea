# 🦜 Kea: Distributed Autonomous Research Engine (DARE)

> **"Not just a Chatbot. A Research Factory."**

---

## 🔌 MCP Tool Calling Standard

Kea adopts the **Model Context Protocol (MCP)** as its universal tool calling interface. MCP enables:

- **Parallel Tool Execution:** Multiple MCP servers run simultaneously, allowing the orchestrator to invoke scraping, analysis, and vision tools concurrently
- **Standardized Communication:** JSON-RPC 2.0 over stdio/SSE provides consistent request/response patterns across all tools
- **Dynamic Discovery:** Tools self-register their capabilities, allowing hot-swapping and runtime extension
- **Isolated Execution:** Each MCP server runs in its own process/container, ensuring fault isolation
- **Scalable Registry ("Jarvis"):** Semantic search (RAG) enables the Planner to utilize 1,000+ tools without context window overflow

### Scalable Tool Discovery ("Jarvis" Registry)
Kea v3.3 introduces a **Persistent Tool Registry** to handle large-scale tool ecosystems (1,000+ tools).
- **Problem**: Injecting 1,000 JSON schemas into the System Prompt is impossible/expensive.
- **Solution**:
    1.  **Indexing**: On startup, Kea incrementally indexes tools into a local **PostgreSQL** database (via `pgvector`).
    2.  **Retrieval**: The Planner uses semantic search to find the "Top-20" most relevant tools for the specific query.
    3.  **Injection**: Only relevant schemas are injected into the context.
    4.  **Zero-Maintenance**: The system automatically hashes and updates the registry on startup. No manual sync required.

### MCP Architecture Overview
**"Pure MCP" & JIT Execution**:
Kea uses a **Pure MCP** architecture. The Orchestrator has *zero* tool code dependencies and delegates all execution to the **MCP Host Service**.
- **JIT (Just-In-Time)**: Tools are ephemeral. When a tool is called, Kea uses `uv` to spawn a pristine environment with exact dependencies.
- **Registry-First**: The Orchestrator discovers tools via the `PersistentToolRegistry` (Postgres), ensuring it can handle 1,000+ tools without bloating prompt context.

```mermaid
sequenceDiagram
    participant Planner as Orchestrator (Brain)
    participant Registry as Jarvis Registry (Postgres)
    participant Host as MCP Host (Hands)
    participant Tool as Ephemeral Tool (Process)

    Note over Planner, Registry: Phase 1: Discovery
    Planner->>Registry: Search("Analyze mining data")
    Registry-->>Planner: Returns [Scraper, Python, Analysis] Schemas
    
    Note over Planner, Host: Phase 2: Execution
    Planner->>Planner: Select Tool: Scraper
    Planner->>Host: POST /tools/call (Tool="Scraper", Args={...})
    
    Host->>Registry: Get Config (Image, Envs, Dependencies)
    Registry-->>Host: {cmd: "uv run...", env: {...}}
    
    Note over Host, Tool: Phase 3: JIT Spawning
    Host->>Tool: uv run --with playright python server.py
    Tool-->>Host: JSON-RPC Ready
    Host->>Tool: Execute(Args)
    
    Tool-->>Host: Stream Progress...
    Tool-->>Host: Return Result
    
    Host-->>Planner: Final ToolResult
```


### MCP Message Flow

```
┌─────────────────┐    JSON-RPC 2.0    ┌─────────────────┐
│   Orchestrator  │ ←───────────────→  │   MCP Server    │
│   (MCP Client)  │                    │   (Tool Host)   │
└─────────────────┘                    └─────────────────┘
        │                                      │
...
```

## 🚀 Running the Services (Verified Config)

To run the system with the new split-port architecture (to avoid conflicts):

### 1. Run the "Multibagger Hunt" (Stress Test)
The easiest way to see Kea in action is to run the stress test, which spins up the full architecture including the Tool Registry.

```bash
# Windows (PowerShell)
python tests/stress/stress_test.py --query=21 --concurrent

# Linux/Mac
python tests/stress/stress_test.py --query=21 --concurrent
```

### 2. Manual Start (Fractal Microservices)
If you need to run services individually, use the following commands. Note that `API_PORT` is no longer used; ports are managed by `shared.service_registry`.

**API Gateway (Port 8000)**
```bash
python -m services.api_gateway.main
```

**Orchestrator (Port 8001)**
```bash
python -m services.orchestrator.main
```

**MCP Host (Port 8002)**
```bash
python -m services.mcp_host.main
```

**RAG Service (Port 8003)**
```bash
python -m services.rag_service.main
```

**Vault (Port 8004)**
```bash
python -m services.vault.main
```

**Swarm Manager (Port 8005)**
```bash
python -m services.swarm_manager.main
```

### Key TCP Ports
| Service | Port | Description |
|:--------|:-----|:------------|
| **API Gateway** | `8000` | Public Entrypoint (Auth & Routing) |
| **Orchestrator** | `8001` | Research & Reasoning Engine |
| **MCP Host** | `8002` | Tool Execution Host |
| **Vault** | `8004` | Audit & Memory Storage |
| **Swarm Manager** | `8005` | Compliance & Governance |
| **Chronos** | `8006` | Scheduling & Time |
| **Python MCP** | `Stdio` | Subprocess (No Port) |


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

- **Fault Tolerance**: Circuit breakers and exponential backoff handling server restarts.

### "Systemic Agentic AI"
Kea is not just a tool-caller; it is a **Resourceful Engineer**.
- **Improvisation**: If a specific tool is missing, the Planner ("Tony Stark" mode) autonomously writes Python scripts to build the tool on the fly.
- **Scalability**: The **Persistent Tool Registry** allows the system to index and retrieve from thousands of tools using semantic search, treating tool discovery as a RAG problem.

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

## 📁 Project Directory Structure

```
kea/
├── 📁 services/                                # Microservices (The Core)
│   │
│   ├── 📁 orchestrator/                        # [BRAIN] Main Orchestrator (Reasoning & Planning)
│   │   ├── README.md                           # 📖 Service Documentation
│   │   ├── main.py                             # FastAPI entrypoint (Port 8001)
│   │   ├── 📁 core/                            # Graph Logic & Pipeline
│   │   └── 📁 nodes/                           # LangGraph Nodes
│   │
│   ├── 📁 api_gateway/                         # [DOOR] API Gateway (Routing & Auth)
│   │   ├── README.md                           # 📖 Service Documentation
│   │   ├── main.py                             # Entrypoint (Port 8000)
│   │   └── 📁 routes/                          # Route definitions
│   │
│   ├── 📁 mcp_host/                            # [HANDS] MCP Tool Host (Execution)
│   │   ├── README.md                           # 📖 Service Documentation
│   │   ├── main.py                             # Entrypoint (Port 8002)
│   │   └── 📁 core/                            # Tool Manager & Parallel Executor
│   │
│   ├── 📁 vault/                               # [MEMORY] The Vault (Storage & Audit)
│   │   ├── README.md                           # 📖 Service Documentation
│   │   ├── main.py                             # Entrypoint (Port 8004)
│   │   └── 📁 core/                            # Vector Store, Audit Trail, Checkpoints
│   │
│   ├── 📁 swarm_manager/                       # [CONSCIENCE] Governance & Oversight
│   │   ├── README.md                           # 📖 Service Documentation
│   │   ├── main.py                             # Entrypoint (Port 8005)
│   │   └── 📁 core/                            # Compliance, Guards, Supervisor
│   │
│   ├── 📁 chronos/                             # [TIME] Chronos (Scheduling & Time)
│   │   ├── README.md                           # 📖 Service Documentation
│   │   ├── main.py                             # Entrypoint (Port 8006)
│   │   └── 📁 core/                            # Job Scheduling logic
│   │
│   └── 📁 shared/                              # [COMMON] Shared Utilities
│       ├── service_registry.py                 # 🕸️ Service Discovery & Ports
│       └── ...
│
├── 📁 mcp_servers/                             # [TOOLS] 17 MCP Tool Servers
│   ├── README.md                               # 📖 Tool Catalog
│   ├── 📁 scraper_server/                      # 🕷️ Web scraping (fetch, browser, PDF)
│   ├── 📁 python_server/                       # 🐍 Code execution (sandbox)
│   ├── 📁 search_server/                       # 🔍 Web search (Tavily, Brave)
│   ├── 📁 vision_server/                       # 👁️ OCR & chart reading
│   ├── 📁 analysis_server/                     # 📊 Statistical analysis
│   ├── 📁 academic_server/                     # 📚 Semantic Scholar, arXiv
│   ├── 📁 document_server/                     # 📄 Document processing
│   ├── 📁 crawler_server/                      # 🕸️ Site crawling
│   ├── 📁 data_sources_server/                 # 📡 External APIs
│   ├── 📁 regulatory_server/                   # ⚖️ Legal/regulatory data
│   ├── 📁 analytics_server/                    # 📈 Data analytics
│   ├── 📁 ml_server/                           # 🤖 ML model inference
│   ├── 📁 qualitative_server/                  # 📋 Qualitative analysis
│   ├── 📁 browser_agent_server/                # 🌐 Browser automation
│   ├── 📁 security_server/                     # 🔒 Security scanning
│   ├── 📁 visualization_server/                # 📉 Chart generation
│   └── 📁 tool_discovery_server/               # 🔎 Dynamic tool discovery
│
├── 📁 shared/                                  # [COMMON] Shared Utilities
│   ├── README.md                               # 📖 Common Libs Doc
│   ├── 📁 llm/                                 # LLM Provider Abstraction
│   ├── 📁 mcp/                                 # MCP Protocol SDK
│   ├── 📁 hardware/                            # Hardware detection
│   ├── 📁 logging/                             # Structured logging
│   ├── 📁 schemas.py                           # Pydantic data models
│   └── environment.py                          # Config loader
│
├── 📁 workers/                                 # Background Workers
├── 📁 tests/                                   # Test Suite
├── docker-compose.yml                          # Full stack local
├── pyproject.toml                              # Python dependencies
└── README.md                                   # This file
```

---

## 📋 Development Status

### ✅ Current State (v2.8)

All core components implemented and functional:

| Component | Status | Description |
|:----------|:------:|:------------|
| **Orchestrator** | ✅ | LangGraph state machine, research pipeline |
| **RAG Service** | ✅ | External Knowledge Engine, Hugging Face ingestion |
| **17 MCP Servers** | ✅ | Scraper, Python, Search, Vision, Analysis, + 12 more |
| **LLM Integration** | ✅ | OpenRouter, query classification, agent personas |
| **Hardware Adaptation** | ✅ | Auto-detect CPU/RAM/GPU, graceful degradation |
| **Agent System** | ✅ | Generator/Critic/Judge consensus, agent spawning |
| **Conversational Memory** | ✅ | Intent detection (DEEPER/REVISE/NEW), context injection |
| **Curiosity Engine** | ✅ | WHY questions, WHAT-IF scenarios |
| **Audit Trail** | ✅ | SQLite logging, checkpointing |
| **API Gateway** | ✅ | 8 route modules, JWT auth, rate limiting |
| **Test Suite** | ✅ | Unit, integration, stress tests |

### Known Limitations

1.  **Environment Specificity**: MCP Server auto-start in `main.py` assumes a standard environment; Docker setups may require adjusting `mcp_servers.yaml`.
2.  **Latency**: Pure MCP architecture introduces slight IPC overhead compared to direct function calls.

### 🏗️ Architecture Principles

| Principle | Description |
|-----------|-------------|
| **Systemic AI** | Self-multiplying agent swarm with dynamic system prompts |
| **Pure MCP** | NO direct imports. All tools communicate via JSON-RPC over Stdio |
| **JIT Execution** | `uv run --with ...` provides ephemeral, isolated environments for each server |
| **Zero-Setup** | Servers self-bootstrap their own dependencies on startup |
| **Hardware Efficiency** | Runs on VPS KVM2 / Colab / Kaggle |
| **Conversational** | Follow-up, not restart—detect intent |
| **Smart Context** | Inject relevant facts + pointers |

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
>
> *For detailed component implementation, please refer to:*
> - **[🧠 Orchestrator & Agents](services/orchestrator/README.md)**  
> - **[💾 Memory & RAG](services/rag_service/README.md)**  
> - **[🔌 MCP Tool Catalog](mcp_servers/README.md)**  
> - **[🚪 API & Queues](services/api_gateway/README.md)**
> - **[📚 Shared Libraries](shared/README.md)**

**Kea** is a microservice-based, recursive AI architecture designed for open-ended domain investigation. Unlike linear RAG systems, Kea utilizes a **Cyclic State Graph** to mimic human research behavior: formulating hypotheses, gathering data, verifying consistency, and autonomously reformulating strategies when results are suboptimal.

It separates **Reasoning** (The Brain/LLM) from **Execution** (The Muscle/Python), ensuring mathematical precision and hallucination-proof results.

---

## 🗺️ 1. The General Architecture (Fractal Corp - 7 Services)

The system follows a **Fractal Microservices Architecture**, dividing cognition into distinct functional areas. This "Split-Brain" design ensures separation of concerns between Reasoning, Execution, Memory, and Oversight.

```mermaid
graph TD
    %% -- External World --
    User[User / Client] -->|HTTP/1.1 REST| Gateway
    
    %% -- INTERFACE LAYER --
    subgraph "API Gateway Service (Port 8000)"
        Gateway[FastAPI App]
        Auth[Auth Middleware]
        Limiter[Rate Limiter]
        Gateway --> Auth --> Limiter
    end
    
    %% -- COGNITIVE LAYER (The Brain) --
    subgraph "Orchestrator Service (Port 8001)"
        OrchAPI[FastAPI Endpoint]
        
        subgraph "LangGraph State Machine"
            Planner[Planner Node]
            Researcher[Researcher Node]
            Keeper[Keeper Node]
            Synthesizer[Synthesizer Node]
        end
        
        OrchAPI --> Planner
        Planner --> Researcher
        Researcher --> Keeper
        Keeper --"Refine"--> Researcher
        Keeper --"Approved"--> Synthesizer
    end
    
    %% -- EXECUTION LAYER (The Hands) --
    subgraph "MCP Host Service (Port 8002)"
        MCPAPI[FastAPI Endpoint]
        ToolMgr[Tool Manager]
        RegistryClient[Registry Client]
        
        subgraph "Process Isolation"
            Scraper[Scraper Process]
            Python[Python Sandbox]
            Search[Search Process]
        end
        
        MCPAPI --> ToolMgr
        ToolMgr -->|Sync| RegistryClient
        ToolMgr -->|JSON-RPC Stdio| Scraper
        ToolMgr -->|JSON-RPC Stdio| Python
        ToolMgr -->|JSON-RPC Stdio| Search
    end
    
    %% -- MEMORY LAYER ( The Vault) --
    subgraph "Vault Service (Port 8004)"
        VaultAPI[FastAPI Endpoint]
        AuditLog[Audit Logger]
        VectorDB[(Postgres + pgvector)]
        SQLDB[(Postgres SQL DB)]
        
        VaultAPI --> AuditLog
        VaultAPI --> VectorDB
        VaultAPI --> SQLDB
    end

    %% -- GOVERNANCE LAYER (The Conscience) --
    subgraph "Swarm Manager (Port 8005)"
        SwarmAPI[FastAPI Endpoint]
        Policy[Policy Engine]
        Supervisor[Supervisor Agent]
        
        SwarmAPI --> Policy
        Policy --> Supervisor
    end
    
    %% -- TEMPORAL LAYER (Time) --
    subgraph "Chronos Service (Port 8006)"
        ChronosAPI[FastAPI Endpoint]
        Scheduler[apscheduler]
        JobQueue[Job Queue]
        
        ChronosAPI --> Scheduler --> JobQueue
    end

    %% -- SERVICE WIRING --
    Limiter -->|HTTP Route| OrchAPI
    Limiter -->|HTTP Route| MCPAPI
    
    Researcher -->|HTTP POST /tools/call| MCPAPI
    Researcher -->|HTTP POST /audit| VaultAPI
    Planner -->|HTTP POST /audit| VaultAPI
    
    ToolMgr -->|HTTP POST /compliance| SwarmAPI
    
    JobQueue -->|HTTP POST /jobs/trigger| OrchAPI

    %% -- STYLING --
    style Gateway fill:#e1f5fe,stroke:#01579b
    style OrchAPI fill:#f3e5f5,stroke:#4a148c
    style MCPAPI fill:#e8f5e9,stroke:#1b5e20
    style VaultAPI fill:#fff3e0,stroke:#e65100
    style SwarmAPI fill:#ffebee,stroke:#b71c1c
    style ChronosAPI fill:#fff8e1,stroke:#fbc02d
```

### The 6 Core Services (Plus Gateway)

1. **API Gateway (Port 8000)**: The single entry point. Handles Auth, Rate Limiting, and routing to internal services.
2. **Orchestrator (Port 8001)**: The "Brain". Runs the LangGraph state machine, plans research, and synthesizes results. It contains *zero* tool code.
3. **MCP Host (Port 8002)**: The "Hands". Manages the 17 MCP tools, handles parallel execution, and maintains the Tool Registry.
4. **Vault (Port 8004)**: The "Memory". Centralized storage for Vector Search (pgvector), SQL (Postgres), Audit Logs, and Graph Checkpoints.
5. **RAG Service (Port 8003)**: The "Library". External Knowledge Engine for ingesting and searching Hugging Face datasets.
6. **Swarm Manager (Port 8005)**: The "Conscience". Enforces ISO/SOC2 Compliance, runs the "Kill Switch", and supervises Agent Health.
7. **Chronos (Port 8006)**: The "Timekeeper". Manages scheduled jobs and "Time-Travel" debugging.

---

## 🚦 2. Pipeline Routing Logic

Kea uses a **two-stage routing system** to efficiently handle queries:

### Pre-Routing Classification (`query_classifier.py`)

Before research routing, queries are classified into types:

| Type | Action | Example |
|------|--------|---------|
| **CASUAL** | Direct response (bypass graph) | "Hello", "Thank you" |
| **UTILITY** | Route to utility handler | "Translate this", "Summarize" |
| **RESEARCH** | Route to Path A/B/C/D | Complex research queries |
| **MULTIMODAL** | Handle attachments | Queries with images/files |
| **UNSAFE** | Block with safe response | Harmful content |

### Research Routing (`router.py`)

For RESEARCH queries, the **Intention Router** selects the optimal execution path:

### Path A: The "Memory Fork" (Incremental Research)
*   **Trigger:** User asks a question partially covered by previous research.
*   **Logic:**
    1.  **Introspection:** The Planner decomposes the query into atomic facts ($A, B, C$).
    2.  **Vector Lookup:** Checks `Atomic Facts Table` (pgvector) for $A, B, C$.
    3.  **Gap Analysis:** The system generates a research task *only* for missing facts.
*   **Outcome:** 50-80% reduction in API costs and latency.

### Path B: The "Shadow Lab" (Re-Calculation)
*   **Trigger:** User asks to modify a parameter of a previous result (e.g., "What if growth is 10% instead of 5%?").
*   **Logic:**
    1.  **Artifact Retrieval:** The system retrieves the clean `data.parquet` file.
    2.  **Code Injection:** The system sends the data + the new parameter to the **Python Sandbox**.
    3.  **Execution:** Python recalculates the specific formula.
*   **Outcome:** Instant answer with zero new web scraping.

### Path C: The "Grand Synthesis" (Meta-Analysis)
*   **Trigger:** User asks to combine multiple research jobs (e.g., "Combine the Market Study and the Regulatory Study").
*   **Logic:**
    1.  **Librarian Fetch:** Retrieves job outputs.
    2.  **Schema Alignment:** The **Analyst Agent** writes Python code to normalize columns.
    3.  **Fusion & Conflict Check:** Executes merge and highlights contradictions.

```mermaid
graph TD
    User[User Input] --> Router{Intention Classifier}
    
    subgraph PathA[Path A: Incremental Research]
        Router -->|Follow-up| VectorCheck[Check Atomic Facts DB]
        VectorCheck -->|Found| CacheHit[Retrieve from Memory]
        VectorCheck -->|Missing| GapDetector{Gap Analysis}
        GapDetector --> DeltaPlan[Delta Planner]
    end
    
    subgraph PathB[Path B: Shadow Lab]
        Router -->|Recalculate| Loader[Load parquet Artifact]
        Loader --> Sandbox[Python Sandbox]
    end
    
    subgraph PathC[Path C: Grand Synthesis]
        Router -->|Compare| Librarian[Fetch Job Manifests]
        Librarian --> Alchemist[Schema Alignment]
    end
    
    subgraph PathD[Path D: Deep Research]
        Router -->|New Topic| Planner[Full OODA Loop]
    end
    
    CacheHit --> Synthesizer[Final Synthesis]
    DeltaPlan --> Scraper[Robotic Scraper]
    Scraper --> Synthesizer
    Sandbox --> Synthesizer
    Alchemist --> Synthesizer
    Planner --> Scraper
```

---

## 🧬 3. Sub-Architectures (The "How-To")

### A. The "Keeper" Protocol (Context Immune System)
*Goal: To prevent the "Rabbit Hole" effect and hallucinations.*

```mermaid
sequenceDiagram
    participant Scraper as Robotic Scraper<br/>(mcp_servers/scraper_server)
    participant Quarantine as Quarantine Zone
    participant Keeper as The Keeper<br/>(services/orchestrator)
    participant Brain as Orchestrator

    Scraper->>Quarantine: Ingest Raw Text (Chunked)
    loop Every Chunk
        Quarantine->>Keeper: Send Vector(Chunk)
        Keeper->>Keeper: Calc Cosine Similarity
        alt Similarity < 0.75
            Keeper-->>Quarantine: INCINERATE (Ignore)
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
    Reality --> Trigger{"Divergence Type?"}
    
    Trigger --"Numbers Wrong?"--> AgentA["Data Scientist: Normalize Units"]
    Trigger --"Missing Factor?"--> AgentB["News Scout: Find Disruptions"]
    Trigger --"Bias?"--> AgentC["Judge: Check Source Credibility"]
    
    AgentA --> Synthesis
    AgentB --> Synthesis
    AgentC --> Synthesis
    Synthesis --> FinalReport["Explained Contradiction"]
```

---

## 🚀 4. Parallel Execution Engine (The Muscle)

Kea v3.0 introduces a hardware-aware parallel dispatcher that maximizes throughput:
- **Hardware Detection**: Automatically detects available RAM (e.g., 30GB) and CPU threads to optimize concurrency.
- **Batch Processing**: The Planner groups independent tasks (e.g., "Scrape 500 URLs") into parallel batches.
- **Dynamic Scaling**: Scales from single-thread debug mode to 50+ concurrent agents on high-end servers.

---

## 🛠️ Technology Stack

| Component | Tech | Role |
| :--- | :--- | :--- |
| **Orchestrator** | **Python / LangGraph** | Cyclic state management and consensus loops. |
| **API Interface** | **FastAPI** | Asynchronous microservice communication. |
| **Analysis** | **Pandas / DuckDB** | In-memory SQL/Dataframe manipulation for "Shadow Lab". |
| **Memory** | **PostgreSQL + pgvector** | Unified storage for Atomic Facts, Tool Registry, Embeddings, and Audit Logs. | |
| **Storage** | **Parquet / S3** | Efficient storage of "Artifacts" (Raw DataFrames). |
| **Isolation** | **Docker / E2B** | Sandboxed code execution environment. |
| **Browser** | **Playwright** | Headless, stealthy web scraping with vision capabilities. |

---

## 🧠 5. The Cognitive Core & Workflow Logic

Kea differs from standard agents by implementing a **"Meta-Cognitive" Layer**. It does not simply execute a prompt; it *designs* the prompt required to execute the task, then critiques the result.

### 4.1. The "Meta-Prompt" Layer (System Prompt Definer)

To optimize for **cost** and **accuracy**, Kea uses a hierarchical model strategy. A cheaper "Architect Model" defines the persona for the "Worker Model."

**The Logic:**
1.  **Task Analysis:** The Planner receives a sub-task (e.g., "Extract financial ratios for Adaro 2024").
2.  **Persona Injection:** The Architect generates a specific System Prompt.
3.  **Execution:** The Worker Model runs with this strict persona, reducing hallucinations.

### 4.2. The Consensus Engine (Adversarial Collaboration)

To prevent the "Yes-Man" problem (where AI blindly agrees with the first search result), Kea implements an **Adversarial Feedback Loop**. This simulates a boardroom meeting between three distinct personas.

**The Roles:**
1.  **The Generator (Optimist):** Gathers data and proposes an answer.
2.  **The Critic (Pessimist):** Scans the answer for logical fallacies, missing dates, or weak sources.
3.  **The Judge (Synthesizer):** Decides if the answer is "Market Ready" or needs "Revision."

### 4.3. The OODA Loop (Recursive Planning)

Kea operates on the military **OODA Loop** (Observe, Orient, Decide, Act) to handle "Unknown Unknowns." The plan is not static; it evolves as data is discovered.

*   **Observe:** The system ingests raw data from the web.
*   **Orient:** The **Keeper** compares this data against the user's intent vector.
*   **Decide:** The **Divergence Engine** determines if the hypothesis holds. Pivot if failed.
*   **Act:** The system spawns new sub-agents based on the *new* hypothesis.

### 4.4. Conversational Memory (`conversation.py`)

Kea maintains session continuity with **Intent Detection** and **Smart Context Injection**:

| Intent | Description | Example |
|--------|-------------|---------|
| **FOLLOW_UP** | Continue current topic | "What about China?" |
| **DEEPER** | Explore aspect deeper | "Tell me more about regulations" |
| **REVISE** | Correct or update | "Actually, use 2024 data" |
| **NEW_TOPIC** | Switch to different topic | "Now research renewable energy" |

**SmartContextBuilder**: Only injects relevant facts + recent turns (not entire history).

### 4.5. Curiosity Engine (`curiosity.py`)

Auto-generates exploratory questions to deepen research (Causal Why, Counterfactual, Scenario, Anomaly).

---

## 💾 6. Memory & Data Structures

To support **"Jarvis-like" Recall** and **Meta-Analysis**, Kea utilizes specific data schemas. We do not just store text; we store **Structured Artifacts**.

See **[services/rag_service/README.md](services/rag_service/README.md)** for schema details on Atomic Facts and Artifact Stores.

---

## ⚡ 7. The JIT Execution Engine (Verified)

Kea uses **uv** (a fast Python package manager) to create isolated, ephemeral environments for each tool execution. This allows the system to "invent" its own tools by writing Python scripts and dependencies on the fly.

### 7.1. Zero-Dependency Configuration
Unlike standard monolithic endpoints, Kea's MCP servers are configured in `settings.yaml` to pull their own dependencies at runtime:

```yaml
# Configuration Example
command: "uv run --with pandas --with scikit-learn python -m mcp_servers.ml_server.server"
```
 
 ### 7.2. Execution Flow

```mermaid
sequenceDiagram
    participant Planner as Orchestrator
    participant Host as MCP Host
    participant Server as Python Tool
    participant UV as uv Package Manager

    Planner->>Host: Execute Tool (JSON-RPC)
    Host->>Server: Forward Request
    Server->>UV: uv run --with yfinance python script.py
    UV->>UV: Resolve & Cache (0.1s)
    UV->>Server: Spawn Process (Isolated)
    Server->>Host: Return Result
    Host->>Planner: ToolResult
```

### 7.2. Security Boundaries
*   **No Network Access:** (Optional) Can be flagged to run with `--offline` for pure logic.
*   **Timeouts:** Hard kill after 30s.
*   **Import Restrictions:** Even with JIT, specific dangerous modules (`os.system`, `subprocess`) can be regex-blocked at the source level before execution.

---

## 🤖 8. The Robotic Infrastructure (The "Hands")

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

### 6.2. Politeness & Rate Limiting
To ensure long-term stability and ethical scraping, Kea implements **Domain-Level Throttling** (e.g., Different buckets for google.com vs idx.co.id).

---

## ⏳ 9. Asynchronous Task Management

Deep research takes time (minutes to hours). A standard HTTP request will timeout. Kea uses an **Event-Driven Architecture**.

### 7.1. The "Fire-and-Forget" Pattern
1.  **Client:** POST `/api/v1/jobs`
2.  **API:** Returns `202 Accepted` + `job_id`.
3.  **Queue:** Pushes job to **Redis**.
4.  **Worker:** Picks up job, runs for 45 minutes, updates **PostgreSQL** state.
5.  **Client:** Polls `/api/v1/jobs/{job_id}` or receives Webhook.

### 7.2. Distributed State Machine
Since the process is long, the state must be persisted. We use **LangGraph Checkpointing**. Only state deltas are saved, allowing for resume-on-failure.

---

## 🚢 10. Deployment Strategy

Kea is designed to be **Infrastructure Agnostic**. It runs on a laptop (Colab/Docker) or a cluster (Kubernetes) using the same code base, controlled by Environment Variables.

### 8.1. The Config Switch
We use a centralized configuration loader that detects the environment.

| Feature | Local / Colab Mode | Production / VPS Mode |
| :--- | :--- | :--- |
| **Database** | PostgreSQL (Server) | PostgreSQL (Server) |
| **Queue** | Python `threading` | Redis |
| **Vector DB** | PostgreSQL (pgvector) | PostgreSQL (pgvector) |
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
  db: 
    image: "pgvector/pgvector:pg16"
    volumes: [postgres_data:/var/lib/postgresql/data]
```

---

## 🔌 11. API Interface (The User Layer)

The API follows a **Polymorphic Asynchronous Pattern**.

Please see **[services/api_gateway/README.md](services/api_gateway/README.md)** for the complete API documentation.

---

## 🛡️ 12. Roadmap

### ✅ Completed (v1.0 - v3.0)
- Microservice Architecture, LangGraph cyclic state machine
- 16 MCP Servers, 12 API Routes, 3 Background Workers
- Hardware detection, graceful degradation, circuit breakers
- JIT dependencies with `uv`, tool isolation
- System Prompt Factory (7 domains, 8 task types)
- Agent Spawner, Conversational Memory, Curiosity Engine
- Organization module, Work Units, Message Bus, Supervisor
- Security: ResourceGuard, KillSwitch, rate limiting

### ✅ Completed (v3.1)
- Wire `graph.py` to real `nodes/` and `agents/` modules
- Connect MCP Orchestrator to researcher node
- Full end-to-end research pipeline
- **Pure MCP Refactoring**: Removed all direct tool imports; 100% dynamic routing via JSON-RPC.
- **JIT Execution**: Implemented `uv` integration for on-demand dependency installation.

### ✅ Completed (v3.2)
- **JIT Audit & Hardening**: Audited all 16 servers for dependency correctness.
- **Robust Configuration**: `settings.yaml` now defines isolated `uv run` environments for every server.
- **Self-Healing**: Automated browser installation and dependency injection.

### ✅ Completed (v3.3)
- **Scalable Tool Discovery**: Implemented "Jarvis" Persistent Registry (SQLite + Qwen3-0.6B).
- **Planner Intelligence**: Upgraded "Tony Stark" prompt for improvisation and tool building.
- **Incremental Sync**: Registry auto-updates by hashing schemas (Zero-Maintenance).

### ✅ Completed (v3.4 - Fractal Scaffolding)
- **Service Fission**: Split monolithic Orchestrator into 6 distinct microservices (Orchestrator, Gateway, MCP Host, Vault, Swarm, Chronos).
- **Service Registry**: Implemented centralized port management and discovery.
- **Network Wiring**: Replaced internal Python imports with HTTP API calls between services.

### 🚧 In Progress (v4.0 - User Integration)
- [ ] Refine MCP Lifecycle Management for Docker


### 🔮 Future (v4.0+)
- [ ] Multi-process agent isolation
- [ ] Redis message broker for MessageBus
- [ ] Multi-Kea distributed operations
- [ ] Kubernetes auto-scaling
- [ ] Multimodal (Gemini Flash)
