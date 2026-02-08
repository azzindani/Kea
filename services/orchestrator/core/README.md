# 🧠 Orchestrator Core ("The Engine Room")

This directory contains the core reasoning, planning, and execution logic for the **Kea Orchestrator**. It implements a high-performance, graph-based autonomy system using LangGraph and a custom DAG execution engine.

## 🏗️ Internal Architecture

The Orchestrator Core is responsible for transforming a high-level user query into a series of actionable, parallel-executable tasks.

### Key Components

#### 📋 Planning & Reasoning
- **`graph.py`**: The "Cognitive Skeleton". Defines the cyclical research graph, including nodes for Planning, Researching, Reviewing, and Synthesis.
- **`microplanner.py`**: Decomposes complex queries into atomic research units.
- **`query_classifier.py`**: Determines the "Intention" (Deep Research, Code Lab, Memory Retrieval).
- **`complexity.py`**: Estimates the resource requirements and depth needed for a task.

#### ⚡ Execution Engine
- **`dag_executor.py`**: The high-throughput execution core. It manages the Directed Acyclic Graph of tool calls, handling phase-based parallel execution.
- **`assembler.py`**: The "Node Wires". Handles the input/output mapping between graph nodes and resolves artifact dependencies.
- **`agent_spawner.py`**: Manages the dynamic creation and supervision of "Swarm Agents" during the research phase.
- **`auto_wiring.py`**: Automatically connects tasks based on inferred data dependencies.

#### 🛡️ Reliability & Governance
- **`recovery.py`**: Implements self-healing logic, allowing the graph to retry failed nodes or pivot strategies upon error.
- **`approval_workflow.py`**: Manages Human-in-the-Loop (HITL) checkpoints for high-risk or ambiguous operations.
- **`organization.py`**: Enforces corporate domain logic (Research, Finance, Legal) and department-specific rules.

#### 📦 Context & Data
- **`context_cache.py`**: High-performance in-memory cache for reducing LLM token usage and redundant tool calls.
- **`artifact_store.py`**: Manages the lifecycle of large data assets generated during research.
- **`modality.py`**: Handles multi-modal inputs/outputs within the research flow.

## 🔄 Cognitive Data Flow

1.  **Classification**: `query_classifier` determines if the query is a search, a code task, or a memory look-up.
2.  **Blueprinting**: `microplanner` creates a topological execution plan.
3.  **Execution**: `dag_executor` spawns swarms via `agent_spawner` to fetch data in parallel phases.
4.  **Verification**: The GCJ (Generator-Critic-Judge) loop in `graph.py` ensures fact accuracy.
5.  **Finalization**: Results are synthesized into the final state and persisted via `artifact_store`.

## 🛠️ Development Guidelines

- **Stateless Nodes**: Ensure all nodes in `graph.py` are stateless or rely strictly on the `GraphState` object.
- **Async First**: Use `async/await` for all I/O and sub-process management.
- **Structured Outputs**: Tools and agents should always return structured data (Pydantic models) to ensure `assembler.py` can correctly wire dependencies.
