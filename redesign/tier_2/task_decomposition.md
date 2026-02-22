# Task Decomposition Engine

## Overview
The Task Decomposition Engine is a Tier 2 Cognitive Module. It takes a high-level goal, breaks it down down into sequential and parallel subtasks, and outputs a structured node graph that the Tier 3 Orchestrator can turn into an actionable DAG.

## Architecture & Flow

```mermaid
---
config:
  layout: dagre
---
flowchart TB
    %% Inputs
    subgraph sInputs["Inputs (From OODA/Tier 4)"]
        nGoal["High-Level Goal / Objective"]
        nContext["Current Agent Context"]
    end

    %% T1 Primitives
    subgraph sTier1["Tier 1 Dependencies"]
        nIntent["Intent Extraction"]
        nEntity["Entity Extraction (Constraints)"]
    end

    %% T2 Processing Engine
    subgraph sEngine["Task Decomposition Engine"]
        direction TB
        
        nAnalyze["Analyze Goal Complexity"]
        nSplit["Split into Logical Sub-Goals"]
        nDepCheck["Identify Cross-Task Dependencies"]
        nResourceCheck["Identify Required Skills/Tools"]
        
        nAnalyze --> nSplit
        nSplit --> nDepCheck
        nDepCheck --> nResourceCheck
    end

    %% Outputs
    subgraph sOutputs["Output to Tier 3 (Orchestrator)"]
        nTaskList["Structured Sub-Task List"]
        nGraphProto["Prototypical Task Graph"]
    end

    %% Routing
    nGoal --> nIntent & nEntity
    nContext --> nAnalyze
    nIntent & nEntity --> nAnalyze
    
    nResourceCheck --> nTaskList --> nGraphProto

    %% Styling
    classDef t1 fill:#14532D,stroke:#22C55E,stroke-width:1px,color:#fff
    classDef t2 fill:#064E3B,stroke:#10B981,stroke-width:2px,color:#fff
    classDef out fill:#1E3A8A,stroke:#3B82F6,stroke-width:2px,color:#fff
    
    class sTier1,nIntent,nEntity t1
    class nAnalyze,nSplit,nDepCheck,nResourceCheck t2
    class nTaskList,nGraphProto out
```
