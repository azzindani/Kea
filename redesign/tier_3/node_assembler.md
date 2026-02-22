# Node Assembler

## Overview
Where the **Graph Synthesizer** creates the broad highway the agent travels on (the DAG map), the **Node Assembler** creates the specific cars that drive on it. 

Every node in the DAG needs to be an executable Python function (a `LangGraph Node`) wrapped consistently so the OODA loop can process it without crashing.

## Architecture & Flow

```mermaid
---
config:
  layout: dagre
---
flowchart TB
    %% Context Provided by the Graph Synthesizer
    subgraph sT3["Tier 3: Node Instruction"]
        nInstruction["Assigned T2 Action"]
        nInputSchema["Required Input Schemas"]
        nOutputSchema["Expected Output Schemas"]
    end

    %% T0 Strict Types
    subgraph sT0["Tier 0 Foundations"]
        direction TB
        nT0Schemas["Pydantic State Validation"]
        nT0StandardIO["Standardized Payload & Error Returns"]
    end
    
    %% Assembly Process
    subgraph sAssembler["Node Assembler Factory"]
        direction TB
        
        nWrap["Wrap Call in Standardized IO (Try/Except)"]
        nInject["Inject Telemetry & Trace IDs"]
        nPydanticIn["Hook Schema Validation (Input)"]
        nPydanticOut["Hook Schema Validation (Output)"]
        
        nInstruction --> nWrap
        nWrap --> nInject
        nInject --> nPydanticIn --> nPydanticOut
    end

    %% Final Node State
    subgraph sFinal["Compiled Node (Passed to Planner)"]
        nCallable["Awaitable State Node Function"]
    end

    %% Dependency Routes
    sT3 --> sAssembler
    sT0 -.-> sAssembler
    
    nPydanticOut --> nCallable

    %% Styling
    classDef t0 fill:#451A03,stroke:#F59E0B,stroke-width:1px,color:#fff
    classDef t3 fill:#1E3A8A,stroke:#3B82F6,stroke-width:2px,color:#fff
    
    class sT0,nT0Schemas,nT0StandardIO t0
    class sT3,nInstruction,nInputSchema,nOutputSchema t3
    class sAssembler,sFinal,nCallable t3
```

## Key Abstraction Logic
1. **The Telemetry Injection (Tier 0 Rule)**: Because of the Corporate Kernel rule that "Distrusted components will fail," every single generated node is automatically injected with Telemetry (tracing and logs bounds) by the node assembler. This guarantees Tier 4 execution never loses track of a nested function.
2. **Schema Wrapper (Tier 0 Pydantic)**: A node never begins processing without automatically doing a Tier 0 Pydantic validation on its inputs, acting as an immediate armor against invalid states in the Graph.
