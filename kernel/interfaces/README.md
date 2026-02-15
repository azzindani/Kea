# 🧠 Kernel Interfaces (The Connective Tissue)

The **Kernel Interfaces** subsystem defines the formal contracts and protocols that allow the Kea Kernel to interact with external services and human supervisors without creating tight coupling.

## 📐 Architecture

Interfaces use Python's `Protocol` and `runtime_checkable` features to implement a **Pure Dependency Injection** model. The Kernel only ever speaks "Interface", and the microservices (Body) provide the "Implementation" at runtime.

### Component Overview

| Component | Responsibility | Key File |
| :--- | :--- | :--- |
| **Fact Store** | Protocol for RAG (Retrieval-Augmented Generation). Allows searching and adding atomic facts. | `fact_store.py` |
| **Tool Registry** | Protocol for discovering and executing MCP (Model Context Protocol) tools. | `tool_registry.py` |
| **Supervisor** | Protocol for quality oversight, human-in-the-loop requests, and escalations. | `supervisor.py` |

---

## ✨ Key Features

### 1. Implementation Decoupling
The kernel has **zero** imports from `services.rag_service` or `services.mcp_host`. Instead, it defines what it *needs* in `FactStore` and `ToolRegistry`. This allows the kernel to be tested in isolation or swapped out for different implementations (e.g., a mock store for CI/CD) without changing a single line of core reasoning logic.

### 2. Runtime Registration
Implementations are registered at service startup via `register_fact_store()` or `register_tool_registry()`. The `KernelCell` then retrieves these via standard `get_*` patterns, ensuring a clean and traversable dependency graph.

### 3. Escalation Protocols
The `Supervisor` interface defines how a cell should handle failure. If a cell cannot meet its quality gate, it calls the supervisor to:
- Request human clarification.
- Trigger a higher-level organizational review.
- Log a critical failure to the governance layer.

---

## 📁 Component Details

### `fact_store.py`
Defines the `AtomicFact` retrieval contract. It supports:
- `search(query, limit)`: Semantic retrieval of prior knowledge.
- `add(fact)`: Persistent storage of new discoveries.

### `tool_registry.py`
Defines the bridge to the MCP ecosystem. It manages:
- Tool discovery across multiple JIT servers.
- Parameter validation against JSON schemas.
- Execution routing to the correct microservice.

---
*Interfaces in Kea ensure that the "Brain" remains portable and untainted by the shifting infrastructure of the "Body".*
