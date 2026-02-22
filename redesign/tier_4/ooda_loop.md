# The OODA Loop (Execution Engine)

## Overview
The OODA Loop (Tier 4) is the real-time beating heart of the Human Kernel. It is responsible for bridging the gap between Kea's internal cognition and the external world. Instead of calculating *how* to solve a problem (Tier 2/3), it simply dictates *when* things happen, *what* state we are currently in, and reacts immediately to environmental changes.

**CRITICAL RULE**: The OODA Loop must never block synchronously on slow LLM calls. The loop must iterate rapidly, dispatching asynchronous tasks and relying on Short-Term Memory to track the state of those operations.

## Architecture & Flow

```mermaid
---
config:
  layout: dagre
---
flowchart TB
    %% External Interfaces (The World)
    subgraph sWorld["Environment"]
        direction TB
        nMCP["MCP Host (Tools/APIs)"]
        nRAG["RAG Service (Knowledge)"]
        nUser["User / Event Messages"]
    end

    %% Fast Memory Cache
    subgraph sMem["Short-Term Memory (RAM)"]
        direction TB
        nContext["Working Context Buffer"]
        nHistory["Recent Loop History"]
    end

    %% T3 Abstraction (Black Box Planner)
    subgraph sT3["Tier 3 Planner"]
        nT3Plan["Graph Synthesizer / JIT Assembly"]
    end

    %% T4 Core Engine - The OODA Loop
    subgraph sT4["Tier 4: OODA Loop Container"]
        direction TB
        
        nObserve["1. Observe"]
        nOrient["2. Orient"]
        nDecide["3. Decide"]
        nAct["4. Act"]
        
        %% Loop flow
        nObserve --> nOrient --> nDecide --> nAct -->|Next Tick| nObserve
    end

    %% Interactions
    nWorldEvents["World State Changes"] -.-> nObserve
    nUser & nMCP --> nObserve
    nObserve --> nHistory

    nOrient <--> nRAG
    nOrient <--> nContext
    
    nDecide -- "Request Plan" --> nT3Plan
    nDecide -- "Evaluate Plan" --> nContext
    nT3Plan -- "Return Executable DAG" --> nDecide
    
    nAct -- "Execute Graph Nodes" --> nMCP

    %% Styling
    classDef t3 fill:#1E3A8A,stroke:#3B82F6,stroke-width:1px,color:#fff
    classDef t4 fill:#312E81,stroke:#6366F1,stroke-width:2px,color:#fff
    classDef mem fill:#0f172a,stroke:#475569,stroke-width:2px,color:#fff
    classDef ext fill:#525252,stroke:#A3A3A3,stroke-width:1px,color:#fff
    
    class sWorld,nMCP,nRAG,nUser,nWorldEvents ext
    class sMem,nContext,nHistory mem
    class sT3,nT3Plan t3
    class sT4,nObserve,nOrient,nDecide,nAct t4
```

## Phase Breakdown

1. **Observe (Sense)**: The Engine rapidly polls or listens to its event stream. Did the user send a new message? Did the RAG database update? Did an MCP tool crash? It drops these events immediately into the `Recent Loop History`.
2. **Orient (Contextualize)**: Looks at the new observations against its `Working Context Buffer` and pulls external knowledge from the `RAG Service`. If the agent was trying to download a file and the observation says "Network Disconnected", the orientation phase updates the state to *Blocked*.
3. **Decide (Plan)**: Compares the Oriented State against its current goals. If the state is *Blocked*, it tosses out the old plan, reaches down to **Tier 3 (The Graph Synthesizer)**, and asks for a new dynamic DAG to handle the disconnect.
4. **Act (Execute)**: Triggers the execution of the active DAG's current nodes. It does not calculate *how* the node works (Tier 2/3 built the node); it simply runs it, pushing the output back into the environment (MCP).
