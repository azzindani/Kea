# Curiosity & Exploration Engine

## Overview
The Curiosity Engine is a Tier 2 Cognitive Module designed to identify "missing" knowledge required to solve a task. Instead of failing when data is absent, the engine autonomously formulates questions and exploration strategies to map out the unknowns before proceeding.

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
        nSchemaState["WorldState (Buffer Context)"]
        nSchemaExplore["ExplorationTask (Query format)"]
    end

    %% DOWNSTREAM TIER 1 IMPORTS (PRIMITIVES)
    subgraph sTier1["Tier 1: Validation Engine"]
        direction LR
        nValidate["PrimitiveValidator.validate_bounds()<br>(validation.md)"]
    end

    %% External Hook (Provided by T3/T4)
    subgraph sTask["Active Context"]
        nTask["Active Sub-Task Execution"]
    end

    %% T2 Processing Engine
    subgraph sEngine["Tier 2: Curiosity Cognitive Engine"]
        direction TB
        
        nGapDetect["1. Detect Missing Variable Vector"]
        nFormulate["2. Formulate Question Strings"]
        nStrategy["3. Route Exploration Strategy<br>(RAG, Web, Scan)"]
        
        nGapDetect --> nFormulate --> nStrategy
    end

    %% Output to Higher Tiers
    subgraph sOut["Output Actions"]
        nActionTask["Generated Exploration Nodes"]
    end

    %% Execution & Routing
    nSchemaState -.->|Formats| nTask
    nTask --> nValidate
    nValidate -- "Constraint Failed (Missing Target Data)" --> nGapDetect
    nValidate -- "Constraint Passed (Data Exists)" --> nBypass["Skip Curiosity Matrix"]
    
    nStrategy -.->|Formats to| nSchemaExplore
    nSchemaExplore --> nActionTask

    %% Styling
    classDef t0 fill:#451A03,stroke:#F59E0B,stroke-width:1px,color:#fff
    classDef t1 fill:#14532D,stroke:#22C55E,stroke-width:2px,color:#fff
    classDef t2 fill:#064E3B,stroke:#10B981,stroke-width:3px,color:#fff
    classDef action fill:#1E3A8A,stroke:#3B82F6,stroke-width:2px,color:#fff
    
    class sTier0,nSchemaState,nSchemaExplore t0
    class sTier1,nValidate t1
    class sEngine,nGapDetect,nFormulate,nStrategy t2
    class sOut,nActionTask action
```
