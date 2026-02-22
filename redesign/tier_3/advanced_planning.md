# Advanced Planning & Tool Binding

## Overview
As part of **Tier 3 (Complex Orchestration)**, managing the precise sequence, expected output, and tool allocation of a DAG map ensures flawless execution in Tier 4. 

- **Hypothesis & Expectation Generation**: For each node assembled, Tier 3 calculates the *expected outcome* (e.g., "File should exist at path X"). If the expectation is not met by Tier 4, it instantly triggers the `Reflection` engine.
- **DAG Sequencing & Prioritization**: Algorithmically orders nodes not just by logical dependency, but by prioritization (fastest vs cheapest vs highest-fidelity paths).
- **Progress Tracker**: A persistent state object that travels with the DAG through loops to map exactly how close the agent is to completing the overarching Task Goal.
- **Tool Selection & Binding**: Matches specific MCP external models (e.g., Python Interpreter, specific vector search query tools) directly into the Node Assembler schema.

## Architecture & Flow

```mermaid
---
config:
  layout: dagre
---
flowchart TB
    %% DOWNSTREAM TIER 0 IMPORTS (SCHEMAS)
    subgraph sTier0["Tier 0: Universal Schemas"]
        direction LR
        nSchema["SubTaskItem Schema"]
        nSchemaTracker["ProgressTracker Model"]
        nSchemaNode["ExecutableNode Schema"]
    end

    %% DOWNSTREAM TIER 2 IMPORTS (COGNITION)
    subgraph sT2["Tier 2 Dependency Model"]
        nTaskDecomp["TaskDecomposer Array<br>(task_decomposition.md)"]
    end

    %% Context Inputs
    subgraph sInput["Incoming Context Constraints"]
        nPriorities["Time/Priority/Budget Constraints"]
    end

    %% Advanced Planner Array
    subgraph sPlanner["Tier 3: Advanced Pipeline"]
        direction TB
        
        nSequence["1. DAG Sequencing & Prioritization<br>(Cost / Speed Router)"]
        nToolMatch["2. Tool Selection & Binding<br>(MCP matching)"]
        nHypothesis["3. Hypothesis Generation<br>(Expected Output Schema)"]
        nTracker["4. Inject Progress Tracker Object"]
        
        nSequence --> nToolMatch --> nHypothesis --> nTracker
    end

    %% Output
    subgraph sOutput["Output"]
        nCompiledNode["Ready Node for Tier 3 Assembler"]
    end

    %% Dependencies
    subgraph sT4["Execution Engine"]
        nT4Observe["OODA Loop Feedback (Failed Expectation)"]
    end

    %% Routing
    sT2 & nPriorities --> nSequence
    nTracker --> nCompiledNode
    nHypothesis <--> nT4Observe
    
    nSchema -.->|Imports| nSequence
    nSchemaNode -.->|Formats| nToolMatch
    nSchemaTracker -.->|Injects| nTracker

    %% Styling
    classDef t0 fill:#451A03,stroke:#F59E0B,stroke-width:1px,color:#fff
    classDef t2 fill:#064E3B,stroke:#10B981,stroke-width:2px,color:#fff
    classDef t3 fill:#1E3A8A,stroke:#3B82F6,stroke-width:3px,color:#fff
    classDef t4 fill:#312E81,stroke:#6366F1,stroke-width:1px,color:#fff
    
    class sTier0,nSchema,nSchemaTracker,nSchemaNode t0
    class sT2,nTaskDecomp t2
    class sPlanner,nSequence,nToolMatch,nHypothesis,nTracker t3
    class sT4,nT4Observe t4
```
