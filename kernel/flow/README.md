# 🧠 Kernel Flow (The Nervous System)

The **Kernel Flow** subsystem manages the logical sequencing and execution patterns of the Kea system. it provides both high-level state machine orchestration (via LangGraph) and low-level dependency-driven task execution (via DAGs).

## 📐 Architecture

Flow is divided into two primary execution layers:
1.  **Macro-Flow (Graphs)**: High-level state transitions and multi-agent interaction loops.
2.  **Micro-Flow (DAGs)**: Granular task dependencies and parallel execution of individual tool calls or sub-steps.

### Component Overview

| Component | Responsibility | Key File |
| :--- | :--- | :--- |
| **Research Graph** | The primary LangGraph state machine. Orchestrates global phase transitions (Plan -> Research -> Critic -> Judge). | `graph.py` |
| **DAG Executor** | Dependency-driven engine. Fires tasks as soon as their specific inputs are ready, enabling non-linear execution. | `dag_executor.py` |
| **Microplanner** | The "Internal Draftsman". Generates detailed step-by-step DAGs for child cells or complex tasks. | `microplanner.py` |
| **Auto-Wirer** | Intelligent data connector. Automatically resolves `input_mapping` between nodes based on artifact types. | `auto_wiring.py` |
| **Workflow Nodes** | Definitions for various execution units (Standard, Loop, Switch, Merge). | `workflow_nodes.py` |

---

## ✨ Key Features

### 1. True Dependency Parallelism
Unlike phase-based systems that wait for all tasks in "Phase 1" to finish before starting "Phase 2", the `DAGExecutor` tracks individual artifact availability. A "Phase 3" task can fire as soon as its specific dependencies from "Phase 1" are satisfied, maximizing hardware utilization.

### 2. Recursive Self-Healing Flow
The `recovery.py` component allows the flow to detect deadlocks or failed branches and trigger "Re-plans" or "Heal-requests" mid-execution. This allows the system to recover from flawed logic or tool failures without restarting the entire cycle.

### 3. Agentic Workflow Library
Provides pre-defined topological patterns:
- **Deep Research**: Comprehensive multi-source analysis.
- **Quick Answer**: Low-latency direct retrieval.
- **Verification**: Dedicated "Red Team" testing of hypotheses.

### 4. Dynamic Node Injection
The `Microplanner` can inject new nodes into a live, running `DAGExecutor` instance. If a task discovers a new information gap (e.g., a hidden company), it can spawn a new research node on-the-fly without breaking the parent graph's structure.

---

## 📁 Component Details

### `graph.py`
The "Macro-Level" brain. Implements the `researcher_node`, `critic_node`, and `judge_node` used in the main LangGraph application.

### `dag_executor.py`
The "Workhorse". Implements the logic for traversing a task graph, handling resource semaphores, and managing artifact passing via the `ArtifactStore`.

### `microplanner.py`
Translates high-level planning instructions into a list of `WorkflowNodes` that the `DAGExecutor` can understand.

---
*Flow in Kea ensures that intelligence is not just linear, but a reactive and adaptive network of concurrent thoughts.*
