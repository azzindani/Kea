# Kea Services Architecture

Kea is built as a modular system of specialized microservices. This directory contains the core logic for each service.

## 🏗️ Core Services

| Service | Directory | Role | Status |
|---------|-----------|------|--------|
| **Orchestrator** | `orchestrator/` | **The Brain**. Handles reasoning, planning, and agent management. Contains the Research Graph and Agent Swarm logic. | 🟢 Active |
| **MCP Host** | `mcp_host/` | **The Hands**. Manages tool execution, hardware governance (Supervisor), and JIT server spawning. | 🟢 Active |
| **API Gateway** | `api_gateway/` | **The Mouth**. Exposes REST/WebSocket endpoints for clients. Handles auth and routing. | 🟢 Active |
| **Vault** | `vault/` | **The Memory**. Secure storage for keys, audit logs, and sensitive session data. | 🟢 Active |
| **RAG Service** | `rag_service/` | **The Knowledge**. Vector database integration (Qdrant) for long-term memory and document retrieval. | 🟢 Active |

## 🔗 Interaction Flow

1.  **User Query** → `API Gateway`
2.  `API Gateway` → `Orchestrator` (Routes via `IntentionRouter`)
3.  `Orchestrator` → `Planner` (Decomposes task)
4.  `Orchestrator` → `MCP Host` (Executes tools via `Supervisor`)
5.  `MCP Host` → `MCP Servers` (Actual execution)
6.  Result → `Orchestrator` (Synthesis) → `API Gateway` → **User**

## ⚙️ Configuration
All services share unified configuration from `d:\Antigravity\Kea\configs\settings.yaml`.
- Models: `config.models.*`
- Timeouts: `config.timeouts.*`
- Governance: `config.governance.*`
