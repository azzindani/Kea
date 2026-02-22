# Tier 3: Complex Orchestration (Planner & Workflow Builder)

## Overview
Tier 3 represents the dynamic graph-building and orchestrating capabilities of the Human Kernel. Think of it as an internal "n8n" or LangGraph workflow generator. It dynamically maps out exactly how an agent will achieve its complex objectives.

**CRITICAL RULE**: Tier 3 utilizes the Cognitive Engines from Tier 2 and maps them as nodes in a directed graph. It generates executable plans. It does not control *when* these sequences are executed (that is the job of Tier 4).

## Scope & Responsibilities
- **Dynamic Workflow Builder**: Acts as the JIT (Just-In-Time) compiler for DAGs, dictating what executes sequentially and what runs in parallel.
- **Node Assembly**: Assembles specific behaviors, tools, and Tier 2 engines into discrete, executable LangGraph state nodes.
- **Dependency Resolution**: Ensures chronological steps have their necessary inputs satisfied by preceding outputs.

## Architecture

```mermaid
flowchart TD
    %% Base dependencies
    subgraph sTier2["Tier 2: Cognitive Engines"]
        nT2["Curiosity & Decomposition"]
    end
    subgraph sTier1["Tier 1: Core Processing"]
        nT1["Primitives"]
    end

    %% T3 Scope
    subgraph sTier3["Tier 3: Complex Orchestration (`orchestrator/`)"]
        direction TB
        
        nPlanner["Strategic Planner"]
        nDAGGen["DAG / Workflow Synthesizer"]
        nNodeGen["Node Assembler"]
        
        nPlanner --> nDAGGen
        nPlanner --> nNodeGen
        nNodeGen --> nDAGGen
    end

    %% T4 Interface
    subgraph sTier4["Tier 4: Execution Engine"]
        direction TB
        nT4Engine["The OODA Loop"]
    end
    
    %% Dependencies
    nT4Engine == "Executes the DAG" ==> sTier3
    sTier3 == "Calls & Resolves" ==> sTier2
    sTier3 -.-> "Direct Primitive Calls" -.-> sTier1
    
    classDef t1 fill:#14532D,stroke:#22C55E,stroke-width:1px,color:#fff
    classDef t2 fill:#064E3B,stroke:#10B981,stroke-width:1px,color:#fff
    classDef t3 fill:#1E3A8A,stroke:#3B82F6,stroke-width:2px,color:#fff
    classDef t4 fill:#312E81,stroke:#6366F1,stroke-width:1px,color:#fff
    
    class nT1,sTier1 t1
    class nT2,sTier2 t2
    class sTier3,nPlanner,nDAGGen,nNodeGen t3
    class nT4Engine,sTier4 t4
```
