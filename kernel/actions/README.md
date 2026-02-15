# 🧠 Kernel Actions (Motor Control)

The **Kernel Actions** subsystem translates cognitive decisions into physical operations. It manages the execution of tools, the spawning of child agents, and the formal protocols for delegation and peer communication.

## 📐 Architecture

Actions act as the "Hands" of the kernel, providing a unified interface to the external world through MCP (Model Context Protocol) and internal recursive scaling.

### Component Overview

| Component | Responsibility | Key File |
| :--- | :--- | :--- |
| **Agent Spawner** | The "Scaler". Decomposes complex tasks into subtasks and manages JIT child cell creation. | `agent_spawner.py` |
| **Delegation Protocol** | The "Contract". Manages iterative feedback-based delegation between parent and child cells. | `delegation_protocol.py` |
| **Tool Bridge** | The "Interface". Bridges internal tool calls to the external `MCP Host` microservice via REST. | `tool_bridge.py` |
| **Parallel Executor** | The "Concurrency Engine". Manages high-volume tool execution with rate limiting and priority queues. | `parallel_executor.py` |
| **Cell Communicator** | The "Messaging Hub". Handles P2P and hierarchical messaging between different `KernelCell` instances. | `cell_communicator.py` |

---

## ✨ Key Features

### 1. Just-In-Time (JIT) Agent Spawning
The `AgentSpawner` allows the kernel to dynamically scale its reasoning power. It uses a `TaskDecomposer` to split a query (e.g., "Compare 5 stocks") into independent subtasks, which are then executed in parallel by specialized child cells.

### 2. Iterative Delegation Protocol
Unlike simple "fire-and-forget" delegation, Kea uses a multi-round protocol:
- **Phase 1**: Parent delegates tasks to children.
- **Phase 2**: Parent reviews child outputs against quality criteria.
- **Phase 3**: Parent provides feedback and requests revisions if criteria are not met.
- **Conflict Resolution**: The protocol detects and resolves conflicting information between sibling cells.

### 3. Intelligent Tool Bridge & Self-Correction
The `tool_bridge.py` doesn't just forward calls. If a tool fails (e.g., due to a syntax error in arguments), it uses the LLM to **auto-correct parameters** and retry, significantly increasing the reliability of long-running autonomous workflows.

### 4. Hardware-Aware Parallelism
The `ParallelExecutor` and `AgentSpawner` communicate with the `ResourceGovernor` to determine optimal concurrency. If the system is under heavy load, it will automatically reduce its "reach" to prevent host exhaustion.

---

## 📁 Component Details

### `agent_spawner.py`
Contains the `TaskDecomposer` with various strategies:
- **Entity-based**: Map tasks to specific objects.
- **Aspect-based**: Map tasks to different dimensions of a problem.
- **Sequential**: Create a chain of execution.

### `delegation_protocol.py`
Defines the `DelegationState` and the feedback loop logic. It ensures that "The Board" only receives high-quality, verified information from subordinate "Staff".

### `tool_bridge.py`
Provides `create_tool_executor`, which encapsulates the HTTP details of communicating with the `MCP Host` service. It ensures `kernel` remains a pure library without deep service dependencies.

---
*Actions in Kea are structured and accountable, ensuring every external interaction is tracked, budgeted, and verified.*
