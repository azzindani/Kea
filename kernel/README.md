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
| [**Nodes**](./nodes/README.md) | **Specialized Reflexes** | Functional units for Planning, Keeping, and Synthesizing. |
| [**Agents**](./agents/README.md) | **Personas** | Specialized reasoning styles (Generator, Critic, Judge). |
| [**Templates**](./templates/README.md) | **Muscle Memory** | "Golden Path" JSON blueprints for expert workflows. |


---

## 🗺️ Kernel Architecture Diagram

The following diagram illustrates the lifecycle of a "thought" within a `KernelCell` and how it interacts with the broader cognitive subsystems.

```mermaid
graph TD
    %% Global Entry
    UserRequest((User Request)) --> MainEntry[KernelCell.process]
    
    subgraph KernelCell [KernelCell v2.0: The Universal Recursive Unit]
        direction TB
        
        subgraph Safety [Governance & Safety]
            EG[ExecutionGuard] --> TB[TokenBudget]
            RG[ResourceGovernor] --> Escalation[Escalation Severity]
        end

        MainEntry --> Intake[Phase 1: _intake]
        Intake --> IC[InferenceContext]
        
        IC --> Assess{Phase 2: Assess Complexity}
        
        subgraph Complexity [Complexity Analysis Engine]
            CL[classify_complexity] --> Tiers[Trivial | Low | Medium | High | Extreme]
            Tiers --> Modes[Direct | Solo | Delegation]
        end
        
        Assess --> CL
        Modes --> ExecutionChoice{Execution Mode?}
        
        ExecutionChoice -- Solo --> SoloExec[Phase 3a: _execute_solo]
        ExecutionChoice -- Delegation --> DeleExec[Phase 3b: _execute_delegation]
        
        subgraph CognitiveCycle [CognitiveCycle: The Human Thinking Loop]
            direction TB
            PH1[PERCEIVE: Instruction Parsing] --> PH2[EXPLORE: Tool Discovery]
            PH2 --> PH3[FRAME: Restatement & Gaps]
            PH3 --> PH4[PLAN: Step Generation]
            PH4 --> PH5[EXECUTE: Tool/Logic Run]
            PH5 --> PH6[MONITOR: Self-Assessment]
            PH6 --> PH7[ADAPT: Course Correction]
            PH7 --> PH8[PACKAGE: Schema Alignment]
            
            PH5 -- ToolCall --> ToolBridge[MCP Tool Bridge]
            ToolBridge -- Result --> PH5
        end
        
        SoloExec --> CognitiveCycle
        
        subgraph RecursiveDelegation [Iterative Delegation Protocol]
            DP[DelegationProtocol] --> SChild[spawn_child]
            SChild --> ChildCell[[Child KernelCell]]
            ChildCell -- Async Result --> DP
        end
        
        DeleExec --> RecursiveDelegation
        
        subgraph InternalState [State & Communication]
            WM[(WorkingMemory)]
            MB[MessageBus]
            Comm[CellCommunicator]
        end
        
        CognitiveCycle <--> InternalState
        RecursiveDelegation <--> InternalState
        
        Heal[Phase 3.5: _execute_heal]
        CognitiveCycle --> Heal
        RecursiveDelegation --> Heal
        
        subgraph QA [Quality Assurance Gate]
            QGate[Phase 4: _quality_check]
            SC[ScoreCard]
            Cont[ContributionLedger]
        end
        
        Heal --> QGate
        QGate --> Output[Phase 5: _package_output]
    end
    
    Output --> FinalResult((StdioEnvelope))
    
    %% External Intelligence
    IC --> KEI[KnowledgeEnhancedInference]
    KEI --> KR[KnowledgeRetriever]
    KEI --> LLM((LLM Provider))
    
    %% Communication Network
    MB <|--|> Parent((Parent Cell))
    MB <|--|> Peers((Peer Cells))
    
    %% Shared Infrastructure
    MainEntry -.-> WB[(WorkBoard)]
    SoloExec -.-> WB
    RecursiveDelegation -.-> WB
```

---

## 🧠 Core Component Deep-Dive

### 1. `KernelCell` (`core/kernel_cell.py`)
The universal entry point. Every "employee" from Intern to CEO runs this exact code. It manages the high-level phases of the task lifecycle: **Intake**, **Assess**, **Execute**, **Quality**, and **Output**.

### 2. `CognitiveCycle` (`core/cognitive_cycle.py`)
A multi-phase reasoning loop that replaces flat ReAct loops.
- **Perceive/Frame**: Understands context and identifies information gaps.
- **Plan**: Generates a DAG of steps.
- **Execute/Monitor**: Runs steps while self-assessing progress.
- **Adapt**: Corrects course if the original plan fails.

### 3. `ComplexityEngine` (`logic/complexity.py`)
Performs heuristic and LLM-based analysis of tasks to determine the most efficient execution path (Solo vs. Delegation) and sets dynamic hardware/token limits.

### 4. `MessageBus` (`io/message_bus.py`)
A multi-directional asynchronous network. Unlike standard agents that only talk to the user, Kea cells talk **Upward** (Clarify/Escalate), **Downward** (Delegate), and **Lateral** (Peer-to-Peer sharing).

### 5. `KnowledgeEnhancedInference` (`logic/inference_context.py`)
Ensures that every LLM call is "grounded" by injecting:
- **Identity**: Role-specific constraints.
- **Skills**: Verified procedures for the task.
- **Rules**: Corporate compliance and logic standards.
- **Knowledge**: RAG-retrieved data from the Vault.

---

## 🔒 Isolation Rules

To maintain architectural integrity, the `kernel/` directory follows strict rules:
1.  **No Service Imports**: Never import from `services.*`.
2.  **Protocol-Oriented**: All external interaction must happen via [Interfaces](./interfaces/README.md).
3.  **No Local State**: The local filesystem is prohibited; all persistence must go through the registered `Vault` interface.

---
*The Kea Kernel is designed to scale intelligence infinitely through recursive encapsulation and adversarial review.*

