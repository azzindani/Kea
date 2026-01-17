# Shared Libraries ("The Foundation")

This directory contains the **Core Infrastructure** and **Type Definitions** used by all microservices. It ensures consistency across the distributed system (e.g., that the Orchestrator speaks the same API language as the Gateway).

---

## 🏗️ Architecture Role

The `shared/` library acts as the "Standard Library" of Kea.
1.  **Configuration**: Centralized `.env` loading via Pydantic Settings.
2.  **Schemas**: The canonical source of truth for all API contracts.
3.  **Observability**: Unified JSON logging and Tracing.
4.  **Hardware**: Abstractions for interacting with LLM providers.

---

## 📁 Codebase Structure & Reference

| File / Directory | Component | Description | Key Classes/Functions |
|:-----------------|:----------|:------------|:----------------------|
| **`schemas.py`** | **Contracts** | **Critical**. Defines the Pydantic models exchanged between services. | `AtomicFact`, `ResearchState`, `JobRequest` |
| **`config.py`** | **Settings** | Strongly-typed configuration manager. Reads env vars. | `Settings`, `get_settings()` |
| **`logging/`** | **Observability**| JSON-structured logger with request ID propagation. | `get_logger()`, `RequestLoggingMiddleware` |
| **`mcp/`** | **Protocol** | The JSON-RPC 2.0 client implementation. | `MCPOrchestrator`, `ToolRegistry` |
| **`llm/`** | **AI** | Provider abstractions (OpenAI, Anthropic). | `ChatModel`, `get_provider()` |
| **`users/`** | **Auth** | User and Tenant management logic. | `UserManager`, `ApiKeyManager` |

---

## 🔬 Deep Dive: The Lingua Franca

### 1. Research State (`schemas.ResearchState`)
This is the object passed around the Orchestrator's graph.
*   **Attributes**: `query`, `facts` (List), `hypotheses` (List), `report` (Markdown).
*   **Usage**: It allows the Planner to write a plan that the Researcher can read, and the Researcher to write facts that the Generator can read.

### 2. Atomic Fact (`schemas.AtomicFact`)
The unit of knowledge in Kea.
```python
class AtomicFact(BaseModel):
    fact_id: str
    entity: str        # "Nvidia"
    attribute: str     # "Revenue 2024"
    value: str         # "$60 Billion"
    confidence: float  # 0.95
```

### 3. Job Polymorphism (`schemas.JobType`)
Defines the valid modes of operation:
*   `DEEP_RESEARCH`: Standard crawl.
*   `SHADOW_LAB`: Recalculation (Sandbox).
*   `GRAND_SYNTHESIS`: Meta-study.

---

## 🔌 Core Type Reference

These are the primary data structures developer interact with.

### Research Primitives
| Class | Description | Fields |
|:------|:------------|:-------|
| `ResearchStatus` | Enum for job lifecycle. | `PENDING`, `RUNNING`, `COMPLETED` |
| `Source` | Provenance metadata. | `url`, `reliability_score`, `accessed_at` |
| `ToolInvocation` | Audit log for agent actions. | `tool_name`, `arguments`, `result` |

### API Contracts
| Class | Description | Fields |
|:------|:------------|:-------|
| `JobRequest` | Input for `POST /jobs`. | `query`, `depth`, `max_sources` |
| `JobResponse` | Output for `GET /jobs/{id}`. | `job_id`, `progress`, `report` |
| `FactResponse` | Output for `GET /facts`. | `entity`, `attribute`, `value`, `source_url` |
