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

## Function Decomposition

### `run_cognitive_filters`
- **Signature**: `async run_cognitive_filters(task_state: TaskState) -> RefinedState | SanityAlert`
- **Description**: Top-level orchestrator. Runs the attention filter to strip noise, then the plausibility check to verify logical coherence. Returns a `RefinedState` (cleaned, focused goal context) if the task passes both filters, or a `SanityAlert` (with rejection reason and confidence) if the task is implausible, contradictory, or impossible.
- **Calls**: `filter_attention()`, `check_plausibility()`.

### `filter_attention`
- **Signature**: `async filter_attention(task_state: TaskState) -> FilteredState`
- **Description**: Step 1: Attention filtering. Masks irrelevant noise from the incoming task context by computing semantic relevance of each context element against the active goal. Uses Tier 1 `scoring.compute_semantic_similarity()` to rank context elements. Drops elements below the relevance threshold (config-driven), producing a focused `FilteredState` containing only the critical variables for the task.
- **Calls**: Tier 1 `scoring.compute_semantic_similarity()`.

### `check_plausibility`
- **Signature**: `async check_plausibility(filtered_state: FilteredState) -> PlausibilityResult`
- **Description**: Step 2: Sanity checking. Verifies that the filtered goal is logically coherent, factually plausible, and physically achievable given the current world state. Runs Tier 1 intent detection to cross-validate the interpreted goal. Checks for contradictions (e.g., "delete and keep the same file"), impossible constraints, and hallucination indicators. Returns `PASS` with confidence or `FAIL` with specific rejection reasons.
- **Calls**: Tier 1 `intent_sentiment_urgency.detect_intent()`, Tier 1 `scoring.evaluate_reward_compliance()`.
