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
    %% DOWNSTREAM TIER 0 IMPORTS (SCHEMAS)
    subgraph sTier0["Tier 0: Universal Schemas (shared/schemas.py)"]
        direction LR
        nSchemaGoal["Base Model: Goal"]
        nSchemaTask["Base Model: SubTaskItem"]
    end

    %% DOWNSTREAM TIER 1 IMPORTS (PRIMITIVES)
    subgraph sTier1["Tier 1: Cognitive Primitives"]
        direction LR
        nIntent["PrimitiveScorers.detect_intent()<br>(intent_sentiment_urgency.md)"]
        nEntity["EntityRecognizer.extract_entities()<br>(entity_recognition.md)"]
    end

    %% Inputs
    subgraph sInputs["Current Agent Context"]
        nContext["Working World State"]
    end

    %% T2 Processing Engine
    subgraph sEngine["Tier 2: Task Decomposition Layer"]
        direction TB
        
        nAnalyze["1. Analyze Goal Complexity"]
        nSplit["2. Split into Logical Sub-Goals"]
        nDepCheck["3. Build Task Dependency Array"]
        nResourceCheck["4. Map Required Agent Skills"]
        
        nAnalyze --> nSplit --> nDepCheck --> nResourceCheck
    end

    %% Outputs
    subgraph sOutputs["Output to Orchestrator (Tier 3)"]
        nTaskList["Structured Array<br>[SubTaskItem, SubTaskItem]"]
    end

    %% Execution & Routing
    nSchemaGoal -.->|Parsed By| nIntent & nEntity
    nSchemaTask -.->|Formats| nTaskList

    nContext --> nAnalyze
    nIntent & nEntity -->|Signal Output| nAnalyze
    
    nResourceCheck --> nTaskList

    %% Styling
    classDef t0 fill:#451A03,stroke:#F59E0B,stroke-width:1px,color:#fff
    classDef t1 fill:#14532D,stroke:#22C55E,stroke-width:2px,color:#fff
    classDef t2 fill:#064E3B,stroke:#10B981,stroke-width:3px,color:#fff
    classDef out fill:#1E3A8A,stroke:#3B82F6,stroke-width:2px,color:#fff
    
    class sTier0,nSchemaGoal,nSchemaTask t0
    class sTier1,nIntent,nEntity t1
    class sEngine,nAnalyze,nSplit,nDepCheck,nResourceCheck t2
    class sOutputs,nTaskList out
```
