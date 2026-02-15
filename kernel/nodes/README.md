# 🧠 Kernel Nodes (Graph Components)

The **Kernel Nodes** subsystem defines the specialized execution units used within Kea's `LangGraph` research pipelines. Each node acts as a functional block in the state machine, handling a specific phase of the cognitive process.

## 📐 Architecture

Nodes are designed to be **Context-Aware** and **Self-Correcting**. They do not just execute strings; they validate, re-plan, and monitor the health of the research graph in real-time.

### Component Overview

| Node | Responsibility | Key File |
| :--- | :--- | :--- |
| **Planner Node** | The "Draftsman". Decomposes the query into micro-tasks, validates tool schemas, and sets the topological order. | `planner.py` |
| **Keeper Node** | The "Guardian". Monitors iteration limits, detects context drift, and determines if research is "Complete". | `keeper.py` |
| **Synthesizer Node** | The "Editor". Aggregates disparate facts and child agent results into a cohesive final report. | `synthesizer.py` |
| **Divergence Node** | The "Re-aligner". Detects when parallel research branches are contradicting or straying from the original intent. | `divergence.py` |

---

## ✨ Key Features

### 1. Zero-Hallucination Planning
The `PlannerNode` uses a multi-stage validation system:
- **Fuzzy Tool Matching**: Hallucinated names (e.g., `get_data`) are mapped to the closest 2,000+ available tool names in the registry.
- **Strict Schema Injection**: Tool arguments are validated against JSON schemas before the research graph even starts, preventing runtime failures.
- **Auto-Parameter Extraction**: Uses heuristics to pull required variables (Tickers, URLs, Dates) from the global query.

### 2. Context Drift Detection
The `KeeperNode` acts as a watchdog. If the research loop is producing too many iterations without finding new facts, or if the "Conversation Focus" has drifted too far from the initial query, the Keeper triggers a "Graceful Halting" or a "Return to Parent" signal.

### 3. Hierarchical Fact Aggregation
The `SynthesizerNode` doesn't just concatenate strings. It:
- Deduplicates facts across different research branches.
- Ranks citations by confidence.
- Structures the output based on pre-defined report templates.

### 4. Convergence Tracking
The `DivergenceNode` monitors the "Stability" of the answer. Once the Generative-Critic-Judge loop reaches a stable consensus, the node allows the graph to proceed to synthesis, saving on unnecessary LLM tokens.

---

## 📁 Component Details

### `planner.py`
The most complex node in the system. It contains the logic for transforming a natural language request into a fully-wired `ExecutionPlan` with dependencies and fallbacks.

### `keeper.py`
Integrates with the `WorkingMemory` to ensure that the agent "Stay on Topic" throughout long-running autonomous missions.

---
*Nodes in Kea provide the modular building blocks that allow complex, multi-agent reasoning to be managed as a structured state machine.*
