# Plausibility & Attention Filtering

## Overview
These are **Tier 2 Cognitive Engines**. Before the complex orchestrator (Tier 3) starts building an elaborate DAG, Tier 2 runs defensive cognitive checks on the incoming data. 
- **Attention Filtering**: Discards noise and highlights the critical variables necessary for the task context.
- **Plausibility & Sanity Check**: Runs a "common sense" or hallucination-check against the extracted intents to ensure the agent isn't being tricked into an impossible or illogical task.

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
        nSchemaRaw["TaskState Schema"]
        nSchemaRefined["RefinedState Schema"]
    end

    %% DOWNSTREAM TIER 1 IMPORTS (PRIMITIVES)
    subgraph sTier1["Tier 1 Dependencies"]
        direction TB
        nVector["EvaluationScorer.semantic_search()<br>(scoring.md)"]
        nScore["PrimitiveScorers.detect_intent()<br>(intent_sentiment_urgency.md)"]
    end

    %% Inputs
    subgraph sInput["Incoming Context"]
        nRawState["Current Task State Context"]
    end

    %% T2 Processors
    subgraph sTier2["Tier 2: Cognitive Filters"]
        direction TB
        
        nAttention["1. Attention Filter<br>(Masks Irrelevant Noise)"]
        nPlausible["2. Plausibility & Sanity Check<br>(Fact/Logic Verification)"]
        
        nAttention --> nPlausible
    end

    %% Output to T3
    subgraph sTier3["Output to Tier 3"]
        nCleaned["Refined Goal Context"]
        nReject["Sanity Alert / Task Rejection"]
    end

    %% Routing
    nSchemaRaw -.->|Formats| nRawState
    nRawState --> nAttention
    
    nAttention -.->|Calls| nVector
    nPlausible -.->|Calls| nScore
    
    nPlausible -- "Pass" --> nCleaned
    nPlausible -- "Fail" --> nReject
    
    nSchemaRefined -.->|Formats| nCleaned

    %% Styling
    classDef t0 fill:#451A03,stroke:#F59E0B,stroke-width:1px,color:#fff
    classDef t1 fill:#14532D,stroke:#22C55E,stroke-width:2px,color:#fff
    classDef t2 fill:#064E3B,stroke:#10B981,stroke-width:3px,color:#fff
    
    class sTier0,nSchemaRaw,nSchemaRefined t0
    class sTier1,nVector,nScore t1
    class sTier2,nAttention,nPlausible t2
```
