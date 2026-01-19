# 🔌 MCP Host Service ("The Hands")

The **MCP Host Service** is the execution engine of Kea. It is responsible for managing the lifecycle of ephemeral tool processes, handling JSON-RPC communication, and providing a unified HTTP interface for the Orchestrator to execute actions.

---

## 🏗️ Architecture Overview

The MCP Host operates as a **Process Manager** and **RPC Proxy**. It implements the "Pure MCP" architecture where no tool logic resides in the main process.

1.  **Tool Manager**: Validates tools against the **Tool Registry**.
2.  **Process Spawner**: Uses `uv` (JIT) or Docker to launch isolated tool servers.
3.  **RPC Bridge**: Converts HTTP `POST` requests from the Orchestrator into JSON-RPC messages over Stdio/SSE.
4.  **Compliance Guard**: Pre-checks every tool call with **Swarm Manager**.

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
