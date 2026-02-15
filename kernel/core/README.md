# 🧠 Kernel Core (The Cortex)

The **Kernel Core** is the primary reasoning engine of the Kea system. It implements the "Synthetic Organism" philosophy by providing a universal, recursive processing unit that can simulate any level of a corporate hierarchy.

## 📐 Architecture

The Core is designed as a **Recursive Cognitive Environment**. At its center is the `KernelCell`, which utilizes the `CognitiveCycle` to process information and can delegate tasks to child cells mirroring a fractal corporate structure.

### Component Overview

| Component | Responsibility | Key File |
| :--- | :--- | :--- |
| **Kernel Cell** | The "Universal Employee". Recursive processing unit that manages delegation, budgets, and execution state. | `kernel_cell.py` |
| **Cognitive Cycle** | Structural thinking loop. Implements Perception, Framing, Planning, Execution, Monitoring, and Adaptation. | `cognitive_cycle.py` |
| **Node Assembler** | The "Wiring Engine". Resolves data dependencies (JSONPath) between nodes and manages topological execution. | `assembler.py` |
| **Resource Governor** | The "Internal Regulator". Monitors system health (CPU/RAM/VRAM) and enforces token/budget constraints. | `resource_governor.py` |
| **Cognitive Profiles** | The "Identity Layer". Defines reasoning styles and capabilities for different hierarchy levels (Board to Intern). | `cognitive_profiles.py` |

---

## ✨ Key Features

### 1. Universal Recursive Unit (`KernelCell`)
Every node in the thinking process—from a high-level strategic "CEO" to a task-oriented "Intern"—runs the exact same `KernelCell` logic. Behavior is modulated strictly via **Cognitive Profiles**, ensuring a predictable and scalable reasoning architecture.

### 2. Biological Cognitive Cycle
Replaces simple ReAct loops with a multi-phase cognitive process:
- **Perceive**: Intake instructions and identify implicit expectations.
- **Frame**: Define scope boundaries, assumptions, and information gaps.
- **Plan**: Strategize the approach and identify necessary tools or delegations.
- **Execute**: Perform the planned actions (Sequential or DAG-based).
- **Monitor**: Continuous self-assessment of progress and accuracy.
- **Adapt**: Dynamic course correction if the monitor detects drift or failure.

### 3. Artifact-Based Data Flow (`NodeAssembler`)
Implements an n8n-style node wiring system. Nodes pass data via `Artifacts`, and the Assembler resolves complex dependencies using a JSONPath-like syntax (e.g., `{{step_id.artifacts.data.items[0]}}`).

### 4. Hardware-Aware Governance (`ResourceGovernor`)
Protects the host system by monitoring hardware metrics in real-time. It can pause execution, throttle child spawns, or trigger escalations if resource limits are reached.

---

## 📁 Component Details

### `kernel_cell.py`
The fundamental unit of Kea. Handles:
- Recursive child spawning (`spawn_child`).
- Token budget management (`TokenBudget`).
- State persistence and message bus integration.

### `cognitive_cycle.py`
The implementation of the `CognitiveCycle` class. It manages phase transitions and structured outputs for each stage of thought.

### `assembler.py`
Contains the `NodeAssembler`, responsible for:
- Topological sorting of tasks.
- Input mapping resolution.
- Self-healing logic for failed node assemblies.

### `organization.py` & `cognitive_profiles.py`
Define the corporate structure and the specific constraints/prompts for each role in the hierarchy.

---
*This directory contains the essential logic for Kea's autonomous reasoning capabilities.*
