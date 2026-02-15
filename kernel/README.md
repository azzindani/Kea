# 🧠 Kea Kernel

The **Kea Kernel** is the "Autonomous Brain" of the enterprise. It is a pure, isolated logic library responsible for perception, reasoning, and hierarchical planning.

## 🏛️ Philosophy

Kea follows a **"Brain vs. Body"** architecture:
- **The Kernel (Brain)**: Pure logic, memory, and reasoning. Zero external dependencies. Zero side-effects.
- **The Services (Body)**: I/O, Networking, Databases, and Tool implementation.

By isolating the Kernel, we ensure that the core intelligence is portable, testable, and capable of running on everything from a 2-core edge device to a 400-core distributed cluster.

---

## 🏗️ Architecture Map

The Kernel is organized into functional subsystems inspired by cognitive science:

| Subsystem | Cognitive Role | Responsibility |
| :--- | :--- | :--- |
| [**Core**](./core/README.md) | **Stem & Midbrain** | Recursive cell logic (`KernelCell`) and the `CognitiveCycle`. |
| [**Memory**](./memory/README.md) | **Hippocampus** | Structured `WorkingMemory`, fact caching, and context persistence. |
| [**Logic**](./logic/README.md) | **Frontal Lobe** | Complexity triage, inference grounding, and adversarial consensus. |
| [**Actions**](./actions/README.md) | **Motor Control** | Tool bridging, agent spawning, and delegation protocols. |
| [**Flow**](./flow/README.md) | **Nervous System** | DAG execution and LangGraph state machines. |
| [**IO**](./io/README.md) | **Circulatory System** | The `MessageBus` and multi-modal sensory packets. |
| [**Interfaces**](./interfaces/README.md) | **Connective Tissue** | Protocols for RAG, Tools, and Human Supervision. |
| [**Nodes**](./nodes/README.md) | **Specialized Reflexes** | Individual functional units for Planning, Keeping, and Synthesizing. |

---

## 🚀 Key Primitives

### 1. The `KernelCell`
The universal recursive processing unit. Every level of the corporate hierarchy (from Intern to CEO) runs the *exact same* code. Profile metadata determines its role and authority.

### 2. The `CognitiveCycle`
A multi-phase reasoning loop:
`Perceive -> Frame -> Plan -> Execute -> Monitor -> Package`

### 3. The `MessageBus`
A multi-directional asynchronous network allowing cells to talk Upward (Escalate), Downward (Delegate), and Lateral (Collaborate).

---

## 🔒 Isolation Rules
To maintain architectural integrity, the `kernel/` directory follows strict rules:
1.  **No Service Imports**: Never import from `services.*`.
2.  **Protocol-Oriented**: All external interaction must happen via [Interfaces](./interfaces/README.md).
3.  **No Local State**: The local filesystem is prohibited; all persistence must go through the registered `Vault` interface.

---
*The Kea Kernel is designed to scale intelligence infinitely through recursive encapsulation and adversarial review.*
