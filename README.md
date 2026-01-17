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
    Orchestrator[Orchestrator - MCP Client]
    Router[MCP Router - Parallel Dispatcher]
    
    Orchestrator --> Router
    
    subgraph Core[Core Servers]
        S1[scraper_server]
        S2[search_server]
        S3[python_server]
        S4[vision_server]
    end
    
    subgraph Data[Data and Analytics]
        D1[data_sources_server]
        D2[analytics_server]
        D3[ml_server]
        D4[visualization_server]
    end
    
    subgraph Domain[Domain-Specific]
        X1[academic_server]
        X2[regulatory_server]
        X3[document_server]
        X4[qualitative_server]
    end
    
    subgraph Utility[Utility Servers]
        U1[crawler_server]
        U2[browser_agent_server]
        U3[security_server]
        U4[tool_discovery_server]
    end
    
    Router --> Core
    Router --> Data
    Router --> Domain
    Router --> Utility
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
├── 📁 services/                                # Microservices (The Core)
│   │
│   ├── 📁 orchestrator/                        # 🧠 The Brain - Main Orchestrator
│   │   ├── main.py                             # FastAPI entrypoint
│   │   │
│   │   ├── 📁 core/                            # Core Research Pipeline
│   │   │   ├── pipeline.py                     # ConversationResearchPipeline (entry point)
│   │   │   ├── graph.py                        # LangGraph cyclic state machine
│   │   │   ├── router.py                       # Intention Router (Path A/B/C/D)
│   │   │   ├── query_classifier.py             # Query intent classification
│   │   │   ├── consensus.py                    # Adversarial Collaboration Engine
│   │   │   ├── context_cache.py                # L1/L2 caching for research
│   │   │   ├── audit_trail.py                  # SQLite audit logging
│   │   │   ├── agent_spawner.py                # TaskDecomposer & parallel agents
│   │   │   ├── prompt_factory.py               # Dynamic system prompts (7 domains)
│   │   │   ├── conversation.py                 # Intent detection (DEEPER/REVISE/NEW)
│   │   │   ├── curiosity.py                    # WHY/WHAT-IF generation
│   │   │   ├── degradation.py                  # GracefulDegrader for low resources
│   │   │   ├── recovery.py                     # @retry, CircuitBreaker
│   │   │   ├── supervisor.py                   # Agent supervision
│   │   │   ├── compliance.py                   # Regulatory compliance checks
│   │   │   ├── approval_workflow.py            # Human-in-the-loop approvals
│   │   │   ├── kill_switch.py                  # Emergency stop
│   │   │   ├── modality.py                     # Multi-modal routing
│   │   │   └── checkpointing.py                # Job state persistence
│   │   │
│   │   ├── 📁 mcp/                             # ⚡ MCP Client Implementation
│   │   │   ├── client.py                       # MCPOrchestrator (tool calls)
│   │   │   ├── registry.py                     # Tool registry & discovery
│   │   │   └── parallel_executor.py            # Parallel tool invocation
│   │   │
│   │   ├── 📁 nodes/                           # LangGraph Nodes (LLM-connected)
│   │   │   ├── planner.py                      # 📝 Query decomposition (uses LLM)
│   │   │   ├── keeper.py                       # 🛡️ Context drift guard
│   │   │   ├── divergence.py                   # ✨ Abductive reasoning
│   │   │   └── synthesizer.py                  # ✍️ Report generation
│   │   │
│   │   └── 📁 agents/                          # Consensus Agents (LLM-connected)
│   │       ├── generator.py                    # 🤠 The Optimist
│   │       ├── critic.py                       # 🧐 The Pessimist
│   │       └── judge.py                        # ⚖️ The Synthesizer
│   │
│   ├── 📁 rag_service/                         # 💾 The Memory Vault
│   │   ├── main.py                             # FastAPI entrypoint
│   │   └── 📁 core/
│   │       ├── vector_store.py                 # Qdrant abstraction
│   │       └── artifact_store.py               # Blob storage
│   │
│   └── 📁 api_gateway/                         # 🚪 The Front Door
│       ├── main.py                             # FastAPI gateway
│       ├── 📁 routes/                          # 8 route modules
│       │   ├── jobs.py                         # /api/v1/jobs
│       │   ├── memory.py                       # /api/v1/memory
│       │   ├── research.py                     # /api/v1/research
│       │   └── ...
│       └── 📁 middleware/
│           ├── auth.py                         # JWT authentication
│           └── rate_limit.py                   # API rate limiting
│
├── 📁 mcp_servers/                             # 🔌 17 MCP Tool Servers
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
├── 📁 shared/                                  # Shared Utilities
│   ├── 📁 llm/                                 # LLM Provider (OpenRouter, Gemini)
│   │   ├── provider.py                         # Abstract LLM interface
│   │   └── openrouter.py                       # OpenRouter implementation
│   ├── 📁 mcp/                                 # MCP Protocol SDK
│   │   ├── protocol.py                         # JSON-RPC 2.0 types
│   │   └── tool_router.py                      # 1000+ tool routing
│   ├── 📁 hardware/                            # Hardware detection
│   │   └── detector.py                         # CPU/RAM/GPU detection
│   ├── 📁 logging/                             # Structured logging
│   │   ├── structured.py                       # JSON/Console formatters
│   │   └── metrics.py                          # Prometheus metrics
│   ├── 📁 database/                            # Database abstraction
│   ├── 📁 storage/                             # S3/local storage
│   ├── 📁 embedding/                           # Embedding models
│   ├── 📁 conversations/                       # Conversation management
│   ├── 📁 tools/                               # JIT tool loader
│   └── environment.py                          # Environment config
│
├── 📁 workers/                                 # Background Workers
│   ├── research_worker.py                      # Deep Research processor
│   ├── synthesis_worker.py                     # Grand Synthesis processor
│   └── shadow_lab_worker.py                    # Recalculation processor
│
├── 📁 tests/                                   # Test Suite
│   ├── 📁 unit/                                # Unit tests
│   ├── 📁 integration/                         # Integration tests
│   ├── 📁 stress/                              # Stress tests
│   └── conftest.py                             # Pytest configuration
│
├── 📁 configs/                                 # Configuration Files
│   ├── mcp_servers.yaml                        # MCP server registry
│   ├── tools.yaml                              # Tool dependencies (JIT)
│   └── logging.yaml                            # Logging configuration
│
├── docker-compose.yml                          # Full stack local
├── pyproject.toml                              # Python dependencies
└── README.md                                   # This file


---

## 📋 Development Status

### ✅ Current State (v2.8)

All core components implemented and functional:

| Component | Status | Description |
|:----------|:------:|:------------|
| **Orchestrator** | ✅ | LangGraph state machine, research pipeline |
| **17 MCP Servers** | ✅ | Scraper, Python, Search, Vision, Analysis, + 12 more |
| **LLM Integration** | ✅ | OpenRouter, query classification, agent personas |
| **Hardware Adaptation** | ✅ | Auto-detect CPU/RAM/GPU, graceful degradation |
| **Agent System** | ✅ | Generator/Critic/Judge consensus, agent spawning |
| **Conversational Memory** | ✅ | Intent detection (DEEPER/REVISE/NEW), context injection |
| **Curiosity Engine** | ✅ | WHY questions, WHAT-IF scenarios |
| **Audit Trail** | ✅ | SQLite logging, checkpointing |
| **API Gateway** | ✅ | 8 route modules, JWT auth, rate limiting |
| **Test Suite** | ✅ | Unit, integration, stress tests |

### � Known Limitations

1. **Graph Nodes**: `graph.py` uses stub implementations. Real execution requires wiring to `nodes/` and `agents/` modules.
2. **MCP Servers**: Server processes not auto-started; need explicit initialization.
3. **Full Pipeline**: End-to-end research flow requires MCP tools + LLM to be connected in graph nodes.

### 🏗️ Architecture Principles

| Principle | Description |
|-----------|-------------|
| **Systemic AI** | Self-multiplying agent swarm with dynamic system prompts |
| **ARM Modularity** | LangGraph core + optional MCP tool extensions |
| **JIT Dependencies** | `uv` on-demand package install |
| **Tool Isolation** | Each MCP server runs in own process |
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

**Kea** is a microservice-based, recursive AI architecture designed for open-ended domain investigation. Unlike linear RAG systems, Kea utilizes a **Cyclic State Graph** to mimic human research behavior: formulating hypotheses, gathering data, verifying consistency, and autonomously reformulating strategies when results are suboptimal.

It separates **Reasoning** (The Brain/LLM) from **Execution** (The Muscle/Python), ensuring mathematical precision and hallucination-proof results.

---

## 🗺️ 1. The General Architecture (High-Level Map)

The system follows a **Hub-and-Spoke Microservices Pattern**. The central Orchestrator manages the lifecycle of a request, delegating work to specialized, isolated services via gRPC/REST.

```mermaid
graph TD
    User[User / API] --> Gateway[API Gateway]
    Gateway --> Router{Intention Router}
    
    Router -->|Simple| FastRAG[Fast RAG Memory]
    Router -->|Methodology| Provenance[Provenance Graph]
    Router -->|Recalculate| ShadowLab[Shadow Lab]
    Router -->|Deep Research| Orchestrator[Main Orchestrator]
    
    subgraph CognitiveCore[The Cognitive Core]
        Orchestrator --> Planner[Planner and Decomposer]
        Planner --> Keeper[The Keeper]
        Keeper --> Divergence[Divergence Engine]
        Divergence --> Synthesizer[Report Synthesizer]
    end
    
    subgraph Tools[Tool Microservices]
        Scraper[Robotic Scraper]
        Analyst[Python Analyst]
        Meta[Meta-Analysis]
    end
    
    subgraph MemoryVault[Triple-Vault Memory]
        Atomic[Atomic Facts DB]
        Episodic[Episodic Logs]
        Artifacts[Parquet Store]
    end
    
    Orchestrator <--> Scraper
    Orchestrator <--> Analyst
    Divergence <--> Atomic
    Scraper --> Artifacts
    Analyst --> Artifacts
```

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
    participant Scraper as Robotic Scraper
    participant Quarantine as Quarantine Zone
    participant Keeper as The Keeper
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

### 4.4. Conversational Memory (`conversation.py`)

Kea maintains session continuity with **Intent Detection** and **Smart Context Injection**:

| Intent | Description | Example |
|--------|-------------|---------|
| **FOLLOW_UP** | Continue current topic | "What about China?" |
| **DEEPER** | Explore aspect deeper | "Tell me more about regulations" |
| **REVISE** | Correct or update | "Actually, use 2024 data" |
| **NEW_TOPIC** | Switch to different topic | "Now research renewable energy" |
| **COMPARE** | Compare entities | "How does this compare to Tesla?" |
| **CLARIFY** | Ask for explanation | "What do you mean by EBITDA?" |
| **CONFIRM** | Confirm action | "Yes, proceed with the analysis" |

**SmartContextBuilder**: Only injects relevant facts + recent turns (not entire history).

---

### 4.5. Curiosity Engine (`curiosity.py`)

Auto-generates exploratory questions to deepen research:

| Question Type | Purpose | Example |
|--------------|---------|---------|
| **CAUSAL_WHY** | Understand causes | "Why did revenue decline in Q3?" |
| **COUNTERFACTUAL** | Explore alternatives | "What if interest rates stayed at 3%?" |
| **SCENARIO** | Project outcomes | "What if demand grows 15% YoY?" |
| **ANOMALY** | Flag inconsistencies | "Volume up 10% but revenue down - why?" |
| **COMPARISON** | Cross-entity insights | "How does Vale compare to Rio Tinto?" |
| **TREND** | Identify patterns | "Is this decline part of a larger trend?" |
| **GAP** | Find missing info | "What data is missing for a complete picture?" |

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

#### **7. Conversations**
*Multi-turn conversation management with memory.*

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/conversations` | `POST` | Start new conversation session. |
| `/api/v1/conversations/{id}` | `GET` | Get conversation history and context. |
| `/api/v1/conversations/{id}/message` | `POST` | Send message with intent detection. |

#### **8. MCP Tools**
*Managing MCP servers and tool execution.*

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/mcp/servers` | `GET` | List active MCP servers. |
| `/api/v1/mcp/tools` | `GET` | List all available tools across servers. |
| `/api/v1/mcp/tools/{name}/call` | `POST` | Execute a specific tool. |

#### **9. Authentication & Users**
*User management and authentication.*

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/auth/token` | `POST` | Get JWT token. |
| `/api/v1/users` | `GET/POST` | List/Create users. |
| `/api/v1/users/{id}` | `GET/PATCH/DELETE` | User CRUD operations. |

---

## 🛡️ 10. Roadmap

### ✅ Completed (v1.0 - v3.0)
- Microservice Architecture, LangGraph cyclic state machine
- 16 MCP Servers, 12 API Routes, 3 Background Workers
- Hardware detection, graceful degradation, circuit breakers
- JIT dependencies with `uv`, tool isolation
- System Prompt Factory (7 domains, 8 task types)
- Agent Spawner, Conversational Memory, Curiosity Engine
- Organization module, Work Units, Message Bus, Supervisor
- Security: ResourceGuard, KillSwitch, rate limiting

### 🚧 In Progress (v3.1)
- [ ] Wire `graph.py` to real `nodes/` and `agents/` modules
- [ ] Connect MCP Orchestrator to researcher node
- [ ] Full end-to-end research pipeline

### 🔮 Future (v4.0+)
- [ ] Multi-process agent isolation
- [ ] Redis message broker for MessageBus
- [ ] Multi-Kea distributed operations
- [ ] Kubernetes auto-scaling
- [ ] Multimodal (Gemini Flash)

---

