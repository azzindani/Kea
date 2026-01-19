# 🔌 MCP Host Service ("The Hands")

The **MCP Host Service** is the execution engine of Kea. It is responsible for managing the lifecycle of ephemeral tool processes, handling JSON-RPC communication, and providing a unified HTTP interface for the Orchestrator to execute actions.

---

## 🏗️ Architecture Overview

The MCP Host operates as a **Process Manager** and **RPC Proxy**. It implements the "Pure MCP" architecture where no tool logic resides in the main process.

1.  **Tool Manager**: Validates tools against the **Tool Registry**.
2.  **Process Spawner**: Uses `uv` (JIT) or Docker to launch isolated tool servers.
3.  **RPC Bridge**: Converts HTTP `POST` requests from the Orchestrator into JSON-RPC messages over Stdio/SSE.
4.  **Compliance Guard**: Pre-checks every tool call with **Swarm Manager** (Port 8005) before transmission.
5.  **Stability Layer**: Implements **Circuit Breakers** and **Exponential Backoff** to prevent cascading failures from hanging tools.

```mermaid
graph TD
    Orch[Orchestrator] -->|HTTP POST| API[FastAPI Endpoint]
    
    subgraph "MCP Host Service (Port 8002)"
        API --> Manager{Tool Manager}
        Manager -->|Check| Swarm[Swarm Manager<br/>(Compliance)]
        Manager -->|Lookup| Registry[Tool Registry]
        
        Manager -->|Spawn| Spawner[Process Spawner]
    end
    
    subgraph "Isolation Zone"
        Spawner -->|Stdio| T1[Scraper Process]
        Spawner -->|Stdio| T2[Python Process]
    end
    
    T1 -.->|Stream| API
```

---

## 📁 Codebase Structure

| File / Directory | Component | Description |
|:-----------------|:----------|:------------|
| **`main.py`** | **Entry Point** | FastAPI app (Port 8002). Exposes `/tools/call`. |
| **`core/`** | **Logic** | Core tool management. |
| ├── `tool_manager.py` | Controller | Coordination logic. Calls Swarm, Registry, and Spawner. |
| ├── `spawner.py` | Infrastructure | Wraps `subprocess.Popen` with `uv run` commands. |
| ├── `rpc_client.py` | Protocol | Implements MCP JSON-RPC 2.0 Client. |
| └── `registry.py` | Discovery | Syncs with `shared.service_registry` and local DB. |

---

## 🔌 API Reference

### Tool Execution
**POST** `/tools/{tool_name}/call`

Executes a tool. This is the primary endpoint used by the Orchestrator.

**Request:**
```json
{
  "arguments": {
    "url": "https://example.com",
    "depth": 2
  },
  "timeout": 30
}
```

**Response:**
```json
{
  "content": [{"type": "text", "text": "Page content..."}],
  "isError": false
}
```

### Server Management
**GET** `/servers`
List all active/available MCP servers (e.g., `scraper`, `python_sandbox`).

**POST** `/servers/restart`
Force restart a specific tool server (useful if a tool hangs).

---

## 🏗️ Technical Deep Dive

### 1. Enterprise Guardrails (`core/tool_manager.py`)
Before any tool is executed, the MCP Host initiates a synchronous compliance handshake:
- **Operation**: `tool_exec`
- **Context**: Pass-through of tool name and proposed arguments.
- **Outcome**: If the **Swarm Manager** returns `passed: false`, the tool execution is halted, and a "Compliance Blocked" error is returned to the Orchestrator.

### 2. Resilience Architecture
The Host treats tool servers as volatile processes:
- **Circuit Breaker**: Each server (e.g., `scraper`) has its own circuit breaker. If it fails 5 consecutive times, the breaker opens, and all future calls to that server are rejected for 60 seconds to allow the process to recover.
- **Graceful Lifecycle**: When the system shuts down, it attempts `SIGTERM` followed by a 5-second timeout before `SIGKILL`, ensuring file handles and network sockets are closed properly.

### 3. Monitoring & Metrics
Integrated with Prometheus to track:
- `ACTIVE_TOOLS`: Gauge of currently running tool processes.
- `tool_duration_seconds`: Histogram of execution latency.
- `tool_failure_total`: Counter of non-compliant or buggy tool executions.
