# 🦜 Kea: Distributed Autonomous Research Engine (DARE)

> **"Not just a Chatbot. A Research Factory."**

---

## 🔌 MCP Tool Calling Standard

Kea adopts the **Model Context Protocol (MCP)** as its universal tool calling interface. MCP enables:

- **Parallel Tool Execution:** Multiple MCP servers run simultaneously, allowing the orchestrator to invoke scraping, analysis, and vision tools concurrently
- **Standardized Communication:** JSON-RPC 2.0 over stdio/SSE provides consistent request/response patterns across all tools
- **Dynamic Discovery:** Tools self-register their capabilities, allowing hot-swapping and runtime extension
- **Isolated Execution:** Each MCP server runs in its own process/container, ensuring fault isolation

### MCP Architecture Overview

```mermaid
graph TD
    Orchestrator["Orchestrator - MCP Client<br/>(services/orchestrator/mcp/client.py)"]
    Router["MCP Router - Parallel Dispatcher<br/>(services/orchestrator/mcp/parallel_executor.py)"]
    
    Orchestrator --> Router
    
    subgraph Core[Core Servers]
        S1["scraper_server<br/>(mcp_servers/scraper_server)"]
        S2["search_server<br/>(mcp_servers/search_server)"]
        S3["python_server<br/>(mcp_servers/python_server)"]
        S4["vision_server<br/>(mcp_servers/vision_server)"]
    end
    
    subgraph Data[Data and Analytics]
        D1["data_sources_server<br/>(mcp_servers/data_sources_server)"]
        D2["analytics_server<br/>(mcp_servers/analytics_server)"]
        D3["ml_server<br/>(mcp_servers/ml_server)"]
        D4["visualization_server<br/>(mcp_servers/visualization_server)"]
    end
    
    subgraph Domain[Domain-Specific]
        X1["academic_server<br/>(mcp_servers/academic_server)"]
        X2["regulatory_server<br/>(mcp_servers/regulatory_server)"]
        X3["document_server<br/>(mcp_servers/document_server)"]
        X4["qualitative_server<br/>(mcp_servers/qualitative_server)"]
    end
    
    subgraph Utility[Utility Servers]
        U1["crawler_server<br/>(mcp_servers/crawler_server)"]
        U2["browser_agent_server<br/>(mcp_servers/browser_agent_server)"]
        U3["security_server<br/>(mcp_servers/security_server)"]
        U4["tool_discovery_server<br/>(mcp_servers/tool_discovery_server)"]
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

## 📁 Project Directory Structure

```
kea/
├── 📁 services/                                # Microservices (The Core)
│   │
│   ├── 📁 orchestrator/                        # [BRAIN] Main Orchestrator
│   │   ├── README.md                           # 📖 Deployment & Architecture Guide
│   │   ├── main.py                             # FastAPI entrypoint
│   │   ├── 📁 core/                            # Core Research Pipeline
│   │   ├── 📁 mcp/                             # MCP Client Implementation
│   │   ├── 📁 nodes/                           # LangGraph Nodes
│   │   └── 📁 agents/                          # Consensus Agents
│   │
│   ├── 📁 rag_service/                         # [MEMORY] Vector & Artifact Vault
│   │   ├── README.md                           # 📖 Schema & Retrieval Guide
│   │   ├── main.py                             # API entrypoint
│   │   └── 📁 core/
│   │       ├── vector_store.py                 # Qdrant abstraction
│   │       └── artifact_store.py               # Blob storage
│   │
│   └── 📁 api_gateway/                         # [DOOR] API & Async Queue
│       ├── README.md                           # 📖 API Routes & Middleware Guide
│       ├── main.py                             # Gateway entrypoint
│       └── 📁 routes/                          # 8 route modules
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

1. **Hybrid Tool Implementation**: While the architecture is MCP-first, the core research loop currently uses direct imports for critical tools (Search) for performance optimization.
2. **Environment Specificity**: MCP Server auto-start in `main.py` assumes a standard environment; Docker setups may require adjusting `mcp_servers.yaml`.

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

## 🗺️ 1. The General Architecture (High-Level Map)

The system follows a **Hub-and-Spoke Microservices Pattern**. The central Orchestrator manages the lifecycle of a request, delegating work to specialized, isolated services via gRPC/REST.

```mermaid
graph TD
    User[User / API] --> Gateway["API Gateway<br/>(services/api_gateway)"]
    Gateway --> Router{"Intention Router<br/>(services/orchestrator)"}
    
    Router -->|Simple| FastRAG["Fast RAG Memory<br/>(services/rag_service)"]
    Router -->|Methodology| Provenance[Provenance Graph]
    Router -->|Recalculate| ShadowLab["Shadow Lab"]
    Router -->|Deep Research| Orchestrator["Main Orchestrator<br/>(services/orchestrator)"]
    
    subgraph CognitiveCore[The Cognitive Core]
        Orchestrator --> Planner["Planner and Decomposer"]
        Planner --> Keeper["The Keeper"]
        Keeper --> Divergence["Divergence Engine"]
        Divergence --> Synthesizer["Report Synthesizer"]
    end
    
    subgraph Tools[Tool Microservices]
        Scraper["Robotic Scraper<br/>(mcp_servers/scraper_server)"]
        Analyst["Python Analyst<br/>(mcp_servers/python_server)"]
        Meta[Meta-Analysis]
    end
    
    subgraph MemoryVault[Triple-Vault Memory]
        Atomic["Atomic Facts DB<br/>(services/rag_service)"]
        Episodic[Episodic Logs]
        Artifacts["Parquet Store"]
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
| **Memory** | **Qdrant + GraphRAG** | Storage of atomic facts and their relationships. |
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

## 🤖 7. The Robotic Infrastructure (The "Hands")

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

## ⏳ 8. Asynchronous Task Management

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

## 🚢 9. Deployment Strategy

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

The API follows a **Polymorphic Asynchronous Pattern**.

Please see **[services/api_gateway/README.md](services/api_gateway/README.md)** for the complete API documentation.

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

### ✅ Completed (v3.0)
- Wire `graph.py` to real `nodes/` and `agents/` modules
- Connect MCP Orchestrator to researcher node
- Full end-to-end research pipeline

### 🚧 In Progress (v3.1)
- [ ] Refine MCP Lifecycle Management for Docker
- [ ] Optimization of Hybrid Tool Calling

### 🔮 Future (v4.0+)
- [ ] Multi-process agent isolation
- [ ] Redis message broker for MessageBus
- [ ] Multi-Kea distributed operations
- [ ] Kubernetes auto-scaling
- [ ] Multimodal (Gemini Flash)
