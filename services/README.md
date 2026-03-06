# Kea Services — The Microservices Layer

The `services/` directory is the application layer of the Kea system. It translates the pure, framework-agnostic logic of `kernel/` into a robust, scalable distributed system composed of **10 HTTP microservices** and **1 SDK** — all communicating exclusively via bounded HTTP APIs.

Unlike traditional LLM wrappers that combine parsing, execution, and memory into a single monolithic loop, Kea operates as a simulated multi-tiered corporation. Each service embodies a specific role (e.g., CEO, Operations Manager, Factory Worker) with strict boundaries, isolated state, and dedicated resource pools.

---

## Core Design Philosophy

### 1. Strict Separation of Concerns

The most critical rule in Kea is the absolute decoupling of **Cognition** from **Execution**:

- **Cognitive Logic (`kernel/`)** — Pure Python functions. They accept data, perform mathematical scoring, LLM inference, and graph resolution, and emit data. They have zero awareness of web frameworks, HTTP, WebSockets, or databases.
- **Service Wrappers (`services/`)** — FastAPI applications that handle networking, security perimeters (API Gateway), connection pooling (Vault/PostgreSQL), and tool execution (MCP Host). They use `kernel/` as an inner brain but own all real-world state.

### 2. Fractal Scaling

Work is always solved at the lowest possible tier of complexity:

- **SOLO (Tier 7)** — A simple query runs on a single Orchestrator instance.
- **TEAM (Tier 8)** — A moderate task causes Corporate Ops to spawn 3–5 concurrent Orchestrator agents and synthesize their outputs.
- **SWARM (Tier 9/8 + Infra)** — A massive objective triggers the Swarm Manager to provision new Kubernetes pods/Docker containers, distributing hundreds of agents against a dynamically chunked DAG.

### 3. Asynchronous Resilience

Long-running agentic loops are unpredictable. A task might take 50 milliseconds or 5 hours. Therefore:

- **Tier 9 (Gateway)** is stateless and highly parallel — it responds to user polls instantly.
- **Tier 8 (Ops)** is stateful via Vault checkpoints, maintaining long-polling loops without blocking web threads.
- If an Orchestrator agent gets stuck, the Swarm Manager can terminate it without affecting the Corporate Gateway or the client's session.

### 4. Zero-Trust Interaction

Internal service-to-service communication uses strict REST schemas via `ServiceRegistry.get_url()`. The **API Gateway** handles authentication and header injection. Downstream services trust gateway-forwarded headers but maintain cryptographic tenant isolation. No service imports directly from another service's codebase.

---

## Network Topology

```
Client / SDK
    │
    ▼
┌─────────────────────────────────┐
│  API Gateway          :8000     │  Auth, rate limiting, proxy
└──────────────┬──────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌──────────────┐  ┌───────────────────┐
│ Corporate    │  │ Direct API Routes │
│ Gateway :8010│  │ (jobs, memory...) │
└──────┬───────┘  └─────────┬─────────┘
       │                    │
       ▼                    ▼
┌──────────────┐     ┌──────────────┐
│ Corporate    │     │ Orchestrator │
│ Ops    :8011 │────▶│        :8001 │
└──────┬───────┘     └──────┬───────┘
       │                    │
       │              ┌─────▼──────┐
       │              │  MCP Host  │
       │              │      :8002 │
       │              └────────────┘
       │
       ├──▶ Vault         :8004  (session & artifact persistence)
       ├──▶ RAG Service   :8003  (knowledge & semantic search)
       └──▶ Swarm Manager :8005  (governance & infra scaling)

Supporting Infrastructure:
  ML Inference  :8007   ◀── RAG Service, MCP Host (embeddings/reranking)
  Chronos       :8006   ──▶ Orchestrator (scheduled triggers)
```

---

## Service Catalog

| Tier | Service | Port | Persona | Role | State |
|:-----|:--------|:-----|:--------|:-----|:------|
| **9** | `corporate_gateway` | `:8010` | The CEO | Apex entry point. Intent classification, strategy assignment (SOLO/TEAM/SWARM), Gate-In/Gate-Out synthesis. | Stateless |
| **8** | `corporate_ops` | `:8011` | The Manager | Mission lifecycle. DAG construction, sprint planning, workforce matching, agent spawning, quality audits. | Stateful (checkpoints) |
| **7** | `orchestrator` | `:8001` | The Worker | LangGraph state engine. Runs one persona on one task. Generates tool call requests, reflects on outputs. | Ephemeral state |
| **Infra** | `api_gateway` | `:8000` | Security Guard | Perimeter router. JWT auth, rate limiting, CORS, unified proxying to all downstream services. | Stateless |
| **Infra** | `vault` | `:8004` | The Memory | Immutable ledger. PostgreSQL + pgvector. Stores artifact blobs, audit logs, session states, mission checkpoints. | Persistent |
| **Infra** | `rag_service` | `:8003` | The Library | Semantic search. pgvector + ml_inference. Serves cognitive profiles, behavioral rules, skills, procedures. | Persistent |
| **Infra** | `mcp_host` | `:8002` | The Hands | Tool execution. JIT-spawns MCP servers from 60+ available servers (2,000+ tools). Fully sandboxed. | Ephemeral |
| **Infra** | `swarm_manager` | `:8005` | The Conscience | Governance. Compliance checks, kill-switch, tool blacklisting, resource governor, agent escalation. | Stateless |
| **Infra** | `chronos` | `:8006` | The Clock | Temporal triggers. Cron-based scheduling; fires HTTP requests to Orchestrator when tasks are due. | Stateful (timers) |
| **Infra** | `ml_inference` | `:8007` | The Cortex | Model serving. High-performance embedding and reranking (e.g., BGE-M3). GPU-optional, role-configurable. | Compute-heavy |
| **SDK** | `sdk` | — | The Interface | CLI tool and Python API client. Submits jobs, tracks metrics, manages auth. Targets API Gateway `:8000`. | — |

---

## Service Details

### API Gateway — `:8000`

The sole public entry point for all external traffic. Handles security, routing, and protocol normalization.

**Key Routes (`/api/v1/`)**:
| Prefix | Purpose |
|--------|---------|
| `/auth/` | Login, register, token refresh |
| `/users/` | User management |
| `/jobs/` | Job creation, status polling, results, cancellation |
| `/memory/` | Context and memory management |
| `/mcp/` | Tool discovery and execution |
| `/system/` | System information |
| `/artifacts/` | Artifact CRUD |
| `/interventions/` | Human-in-the-loop interventions |
| `/llm/` | Direct LLM inference |
| `/conversations/` | Conversation management |
| `/corporate/` | Proxy to Corporate Gateway |

**Calls**: Orchestrator (8001), MCP Host (8002), RAG Service (8003), Vault (8004), Corporate Gateway (8010)

**Structure**: `routes/`, `middleware/` (auth, rate limiting, security headers), `clients/`

---

### Orchestrator — `:8001`

The execution engine for individual agent tasks. Wraps the kernel's Conscious Observer (Tier 7) in an HTTP service.

> **Status**: Currently in redesign phase. The `/execute` endpoint returns `NOT_IMPLEMENTED` while kernel integration is being refactored. Tool proxying via MCP Host is fully operational.

**Key Endpoints**:
| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Service health |
| `GET /tools` | List available MCP tools (proxies to MCP Host) |
| `POST /execute` | Start a job (redesign in progress) |
| `POST /tools/{tool_name}` | Execute a specific MCP tool |
| `GET /execute/stream` | Stream execution results (redesign in progress) |
| `POST /corporate/agents` | Corporate agent management |

**Calls**: MCP Host (8002)

**Structure**: `routers/` (corporate_agents)

---

### MCP Host — `:8002`

JIT (Just-In-Time) tool execution environment. Manages 60+ MCP servers covering 2,000+ tools across finance, ML, data, web, document processing, and more.

**Key Endpoints**:
| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Health with active server count |
| `GET /tools` | List tools (filterable by server, with limit) |
| `POST /tools/search` | Semantic search for tools via pgvector RAG |
| `POST /tools/sync` | Full tool discovery and RAG registration |
| `POST /tools/execute` | Execute a single tool (ephemeral spawn → run → stop) |
| `POST /tools/batch` | Execute multiple tools in parallel (fan-out) |
| `POST /server/{name}/stop` | Stop a specific server |

**Calls**: ML Inference (8007) for embedding generation during tool search

**Structure**: `core/` — `session_registry.py`, `postgres_registry.py`, `tool_registry.py`

---

### RAG Service — `:8003`

Multi-source knowledge controller. Provides semantic search over the `knowledge/` library, HuggingFace datasets, and atomic insights produced by running agents.

**Key Endpoints**:
| Prefix | Purpose |
|--------|---------|
| `POST /insights` | Add an atomic insight |
| `POST /insights/search` | Search insights by semantic similarity |
| `GET/DELETE /insights/{id}` | Read or delete an insight |
| `POST /datasets/ingest` | Background HuggingFace dataset ingestion |
| `DELETE /datasets/{id}` | Delete a dataset |
| `POST /knowledge/search` | Semantic search over skills, rules, personas |
| `GET /knowledge/{id}` | Retrieve a knowledge item |
| `POST /knowledge/sync` | Sync `knowledge/` markdown files to DB |
| `GET /knowledge/stats/summary` | Knowledge base statistics |

**Calls**: ML Inference (8007) for embeddings and reranking

**Structure**: `core/` — `insight_store.py`, `knowledge_store.py`, `dataset_loader.py`, `artifact_store.py`, `postgres_artifacts.py`

---

### Vault — `:8004`

Immutable persistence layer. All durable state in the system flows through Vault. PostgreSQL + pgvector backend.

**Key Endpoints**:
| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Service health |
| `POST /audit/logs` | Log an audit event |
| `GET /audit/logs` | Query audit logs (by actor, session_id, limit) |
| `POST /persistence/sessions` | Persist execution results to vector store |
| `GET /persistence/query` | Semantic search over stored insights and execution results |

**Calls**: None — Vault is a pure data service; no outbound service calls.

**Structure**: `core/` — `audit_trail.py`, `postgres_store.py`, `postgres_audit.py`, `vector_store.py`

---

### Swarm Manager — `:8005`

Governance and compliance layer. Provides kill-switch emergency stops, tool blacklisting, resource limits, and agent escalation management. Swarm Manager defines policy; it does not directly spawn infrastructure.

**Key Endpoints**:
| Endpoint | Purpose |
|----------|---------|
| `POST /compliance/check` | Check an operation against compliance rules |
| `POST /kill-switch/activate` | Trigger emergency stop for all agents |
| `DELETE /kill-switch` | Resume from emergency stop |
| `GET /kill-switch/status` | Current kill-switch state |
| `POST /kill-switch/blacklist/{tool}` | Temporarily blacklist a tool |
| `DELETE /kill-switch/blacklist/{tool}` | Remove from blacklist |
| `GET /agents` | List pending escalations |
| `POST /agents/{work_id}/resolve` | Resolve an escalation |
| `GET /rate-limits/{agent_id}` | Check remaining rate limit budget |
| `GET /resource/status` | Current CPU/RAM/DB resource governor state |

**Calls**: None

**Structure**: `core/` — `compliance.py`, `kill_switch.py`, `supervisor.py`, `guards.py`, `resource_governor.py`

---

### Chronos — `:8006`

Temporal trigger service. Manages cron-based scheduling. When a scheduled task fires, Chronos sends an HTTP POST to the Orchestrator — identical to a human submitting a job — so it is processed through the full pipeline.

**Key Endpoints**:
| Endpoint | Purpose |
|----------|---------|
| `POST /schedule` | Create a scheduled task (requires cron expression) |
| `GET /schedule` | List all scheduled tasks |
| `DELETE /schedule/{task_id}` | Delete a scheduled task |

**Calls**: Orchestrator (8001) — fires `POST /execute` when a scheduled task triggers

**Structure**: `core/` — `scheduler.py`, `storage.py`, `helpers.py`

---

### ML Inference — `:8007`

Dedicated model serving for embedding generation and document reranking. Configurable via `ML_ROLE` environment variable (`embedding`, `reranker`, `both`, `vl_embedding`, `vl_reranker`). Supports GPU-optional deployment.

**Key Endpoints**:
| Endpoint | Purpose |
|----------|---------|
| `GET /` | Service discovery and metadata |
| `GET /health` | Health with model and device status |
| `GET /v1/models` | List loaded models and their readiness |
| `POST /v1/embed` | Batch text embedding |
| `POST /v1/embed/query` | Single query embedding (convenience) |
| `POST /v1/rerank` | Rerank documents by relevance to a query |

**Calls**: None — pure compute service.

**Structure**: `core/` — `model_pool.py`, `schemas.py`

---

### Corporate Gateway — `:8010`

Tier 9 apex entry point for all corporate-scale operations. Owns the three-phase pipeline:

```
Gate-In:    Intent classification → strategy assignment (SOLO/TEAM/SWARM) → mission decomposition
Execute:    Delegation to Corporate Ops (HTTP)
Gate-Out:   Artifact collection → quality audit → executive synthesis → Vault persistence
```

**Key Endpoints**:
| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Service health |
| `POST /corporate/process` | Unified entry point for all corporate operations |

**Calls**: Corporate Ops (8011), Vault (8004)

**Structure**: `routers/corporate.py`, `clients/corporate_ops.py`, `clients/vault_ledger.py`

---

### Corporate Ops — `:8011`

Tier 8 tactical layer. Receives mission chunks from Corporate Gateway, builds execution DAGs, matches workers to tasks, spawns Orchestrator agents, and runs quality audits on outputs.

**Key Route Groups (`/api/v1/`)**:
| Prefix | Purpose |
|--------|---------|
| `/workforce/` | Agent hiring, firing, scaling, profile matching |
| `/orchestration/` | Mission chunking, DAG construction, sprint execution |
| `/quality/` | Quality metrics, contradiction detection, audit results |

**Calls**: Orchestrator (8001), Vault (8004)

**Structure**: `routers/` — `workforce.py`, `orchestration.py`, `quality.py` | `clients/` — `orchestrator_client.py`, `vault_ledger.py`

---

### SDK — CLI & Python Client

Not an HTTP service. Provides the command-line interface and a Python API client for interacting with Kea programmatically. Targets the API Gateway.

**Components**:

| File | Purpose |
|------|---------|
| `cli.py` | Entry point CLI (`--query`, `--env`, `--url`, `--verbose`) |
| `api.py` | `AutonomousClient` — JWT auth, auto-register/login, `get()`/`post()`/`delete()` |
| `runner.py` | `JobRunner` — orchestrates task submission and result polling |
| `metrics.py` | `MetricsCollector` — tracks job performance metrics |

**Calls**: API Gateway (8000) — `/api/v1/auth/`, `/api/v1/jobs/`

---

## 3-Phase Execution Pipeline

Every request flowing into `POST /corporate/process` undergoes a strict 3-phase lifecycle.

### Phase 1 — Gate-In (Tier 9: Corporate Gateway)

1. **Context Hydration** — Fetches the user's `SessionState` from Vault.
2. **Intent Classification** — Evaluates `ClientIntent`:
   - `STATUS_CHECK` / `FOLLOW_UP` → fast-path returns immediately
   - `INTERRUPT` → forwards abort/scope-change signal to Tier 8
   - `NEW_TASK` / `REVISION` → proceeds to full planning
3. **Strategy Assessment** — Analyzes objective complexity and token budgets; establishes `ScalingMode` (SOLO, TEAM, or SWARM).
4. **Decomposition** — Breaks the goal into atomic `MissionChunks`.

### Phase 2 — Execute (Tier 8: Corporate Ops)

1. **DAG Construction** — Converts `MissionChunks` into a topologically sorted execution graph.
2. **Sprint Planning** — Groups chunks into parallelizable batches (sprints).
3. **Workforce Matching** — Queries RAG Service for the optimal `CognitiveProfile` per chunk.
4. **Agent Spawning** — Issues HTTP calls to Orchestrator to instantiate persona-specific Tier 7 agents.
5. **Checkpointing** — Writes `CheckpointState` aggregates to Vault as sprints complete. Isolated retries on sprint failure.

### Phase 3 — Gate-Out (Tier 9: Corporate Gateway)

1. **Artifact Collection** — Pulls all sprint outputs from Vault.
2. **Quality Audit** — Runs `QualityResolver` pass; detects contradictions between agent outputs.
3. **Executive Synthesis** — Merges dispersed outputs into a cohesive `SynthesizedResponse` with executive summaries and confidence scores.
4. **Ledger Persistence** — Final response and session anchors are persisted to Vault.

---

## End-to-End Data Flow Example

**Request**: *"Analyze our competitor's new product and draft a counter-marketing campaign."*

```
1. Client → API Gateway (8000)
      Auth token validated. Routed to Corporate Gateway.

2. Corporate Gateway (8010) — Gate-In
      Vault: fetch past competitor context.
      Classification: COMPLEX, TEAM strategy.
      Decompose: [1] Web Research, [2] Marketing Draft.
      Dispatch to Corporate Ops.

3. Corporate Ops (8011) — Execute
      RAG Service: fetch "Researcher" and "Marketer" profiles.
      Spawn Agent A → Orchestrator instance (Researcher profile).
      Spawn Agent B → Orchestrator instance (Marketer profile).

4. Orchestrator A (8001)
      MCP Host: web-scraping tools → findings saved as Artifact_A in Vault.

5. Orchestrator B (8001)
      Reads Artifact_A from Vault.
      LLM loops → marketing draft saved as Artifact_B in Vault.

6. Corporate Ops (8011)
      Sprint complete. QualityResolver: audit A vs B.
      Signal success to Corporate Gateway.

7. Corporate Gateway (8010) — Gate-Out
      Pull Artifact_A and Artifact_B from Vault.
      Synthesize executive summary.
      Persist final response to Vault.

8. API Gateway (8000) → Client
      Deliver compiled payload.
```

---

## Service Dependency Map

```
                        ┌────────────────┐
                        │   API Gateway  │ :8000
                        └───────┬────────┘
              ┌─────────────────┼──────────────────┐
              ▼                 ▼                  ▼
     Corporate Gateway    Orchestrator        RAG / Vault / MCP
          :8010               :8001           (direct routes)
              │                  │
              ▼                  ▼
       Corporate Ops          MCP Host
          :8011                :8002
              │                  │
    ┌─────────┤           ┌──────┘
    ▼         ▼           ▼
 Vault    Orchestrator  ML Inference
 :8004      :8001         :8007
              ▲
              │
           Chronos
            :8006
```

**Leaf services** (no outbound HTTP calls): `vault`, `swarm_manager`, `ml_inference`

**Chronos** acts as an automated client — it fires requests into Orchestrator on a schedule, identically to a human-initiated request.

---

## Configuration & Standards

All services follow these mandatory conventions:

| Concern | Implementation |
|---------|---------------|
| **Port config** | All ports centralized in `shared/config.py` `ServiceSettings`; never hardcoded |
| **Service URLs** | All inter-service HTTP calls use `ServiceRegistry.get_url(ServiceName.*)` |
| **Logging** | All services use `get_logger(__name__)` from `shared/logging/main.py` with `RequestLoggingMiddleware` |
| **Health checks** | Every service exposes at minimum `GET /health` |
| **API models** | All request/response bodies use Pydantic models from `shared/schemas.py` or service-local `models/` |
| **Async** | All I/O is `async/await`; blocking calls (`requests`, `time.sleep()`) are forbidden |
| **Resiliency** | External calls use `tenacity` retries with exponential backoff (policy defined in `shared/config.py`) |
