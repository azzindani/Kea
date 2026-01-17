# Shared Libraries

This directory contains common utilities, schemas, and configurations used across all Kea microservices. It is the "glue" that holds the distributed system together.

## ⚠️ Dependency Rule
Code in `shared` must **never** import from `services` or `workers`. It must remain a pure dependency leaf to prevent circular imports.

## 🧩 Codebase Reference

### 1. Core Data Structures (`schemas.py`)
Defines the Pydantic models exchanged between services.

| Class | Description | Usage |
|:------|:------------|:------|
| `GraphState` | **The Context**. TypedDict holding the entire state of a research job (query, facts, plan). | Orchestrator |
| `AtomicFact` | **The Knowledge**. Entity-Attribute-Value model for storing discrete information. | RAG Service |
| `ToolInvocation`| **The Audit**. Record of a tool call, its inputs, outputs, and success status. | Keeper / Logger |
| `ResearchStatus`| **The Progress**. Enum (QUEUED, RUNNING, COMPLETED, FAILED). | API Gateway |

### 2. Configuration (`environment.py`)
Centralized configuration management.

| Class/Function | Description |
|:---------------|:------------|
| `EnvironmentConfig` | Singleton loading `.env` variables. |
| `get_settings()` | Returns typed settings object (Database URL, Redis Host, API Keys). |
| `is_production()` | Helper to toggle debug modes and security checks. |

### 3. Sub-Modules
Specialized utility packages.

| Directory | Description | Key Components |
|:----------|:------------|:---------------|
| `logging/` | **Structured Logging**. Ensures all logs are JSON-formatted with trace IDs for observability (Grafana/Loki). | `get_logger()`, `setup_logging()` |
| `llm/` | **LLM Abstraction**. Unified interface for OpenAI, Anthropic, Gemini, and OpenRouter. Handles retries and cost tracking. | `LLMProvider`, `OpenRouter` |
| `mcp/` | **MCP Protocol SDK**. Shared logic for parsing JSON-RPC messages and routing tool calls. | `ToolRouter`, `JSONRPCMessage` |
| `hardware/` | **Resource Awareness**. Detects available CPU cores, RAM, and GPU (CUDA/MPS) to optimize worker counts. | `HardwareDetector` |
| `database/` | **Persistence**. Async wrappers for PostgreSQL (asyncpg) and Redis. Manages connection pools. | `get_db_pool()`, `run_query()` |

## 🚀 Usage

Import these directly in your services:

```python
from shared.schemas import GraphState
from shared.logging import get_logger

logger = get_logger(__name__)
```
