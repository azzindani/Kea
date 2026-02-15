# 🧠 Kernel Memory (The Hippocampus)

The **Kernel Memory** subsystem manages the persistence and retrieval of cognitive state, artifact storage, and biological-inspired short-term focus. It ensures that every `KernelCell` has exactly the context it needs without overwhelming the system.

## 📐 Architecture

Memory is divided into three distinct layers based on persistence and role:

1.  **Working Memory (L1)**: High-speed, structured active context owned by a single `KernelCell`.
2.  **Context Cache (L2)**: Multi-level (Memory/Disk) caching for cross-cell or cross-session data.
3.  **Artifact Store (L3)**: Persistent storage for node outputs and research findings.

### Component Overview

| Component | Responsibility | Key File |
| :--- | :--- | :--- |
| **Working Memory** | Structured "scratchpad". Tracks focus items, hypotheses, decisions, and local tasks. | `working_memory.py` |
| **Context Cache** | LRU caching system. Manages conversation summaries, facts, and embeddings. | `context_cache.py` |
| **Graceful Degrader** | Resource-aware execution. Throttles parallelism and load under high resource pressure. | `degradation.py` |
| **Error Journal** | Recursive fix tracking. Maintains a DAG of error causality for self-healing loops. | `error_journal.py` |
| **Artifact Store** | Manages the lifecycle of files, reports, and data produced during research. | `artifact_store.py` |

---

## ✨ Key Features

### 1. Miller-Compliant "Focus"
The `WorkingMemory` limits active attention to ~7 **Focus Items** at a time. This prevents "Prompt Poisoning" by ensuring the LLM only ever sees the most relevant sub-problems, hypotheses, and recent observations.

### 2. Multi-Level Context Caching
The `ContextCache` provides a tiered approach:
- **L1 (RAM)**: Sub-millisecond access for active conversation threads.
- **L2 (Disk)**: Process-surviving storage for expensive embeddings and tool results.

### 3. Hypothesis & Decision Ledger
Reasoning isn't just text; it's a series of evaluated **Hypotheses** and formal **Decisions**. The memory system tracks the confidence levels, supporting evidence, and rejected alternatives for every cognitive action.

### 4. Self-Healing Error Journal
Critical for autonomous long-running tasks. If a node fails, the `ErrorJournal` records the failure, linked to the `FixAttempt`. If the fix causes a secondary error, it's tracked in a **Causality DAG**, preventing infinite healing loops.

### 5. Graceful Degradation
Monitoring hardware in real-time. If RAM or CPU spikes, the system automatically:
1. Reduces parallelism (e.g., 4 concurrent workers -> 1).
2. Increases timeouts to account for congestion.
3. Skips optional refinement tasks to prioritize core completion.

---

## 📁 Component Details

### `working_memory.py`
The most complex memory component. It defines:
- `FocusItem`: Atoms of attention (Facts, Questions, Decisions).
- `Hypothesis`: Statements with confidence scores and support/weaken methods.
- `Decision`: Immutable records of rationale.

### `context_cache.py`
Unified caching interface. Supports TTL, size-based eviction (LRU), and prefix-based deletion for grouping related data.

### `degradation.py`
Implements the `GracefulDegrader`, which uses `shared.hardware` alerts to dynamically adjust `max_parallel` and `timeout_multiplier` settings.

---
*Memory in Kea is not just storage; it is active context management targeted for small hardware efficiency.*
