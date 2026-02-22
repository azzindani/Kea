# Confidence & Precision Scoring 

## Overview
As a **Tier 1** module, the Scoring/Evaluation engine does not think; it measures. Following the mandate of evaluating safety and exactness computationally before relying on an LLM, this engine runs pure algorithms (Vector similarity, Cross-encoding, Contextual Weighting) to assess the quality of a specific action relative to an initial goal.

Tier 3 Guardrails and Tier 2 Plausibility checks use this tool precisely to decide if they should reject a DAG or trust an execution result.

## Architecture & Flow

```mermaid
---
config:
  layout: dagre
---
flowchart TB
    %% DOWNSTREAM IMPORTS
    subgraph sTier0["Tier 0: Universal Schemas"]
        direction LR
        nScoreObj["NumericScore Schema"]
    end

    %% Inputs
    subgraph sInput["Incoming Context Container"]
        nInput["Content / Agent Output"]
        nQuery["Original Query / Goal"]
        nMeta["Metadata (Context)"]
    end

    %% TIER 1 CORE
    subgraph sTier1["Tier 1: Hybrid Evaluation Framework"]
        direction TB
        
        %% Track 1: Semantic
        nEmbed["Embedding Engine"]
        nScoreVector["Cosine Similarity Metric"]

        %% Track 2: Precision
        nRerank["Reranker (Cross-Encoder)"]
        nScorePrecise["Relevance / Precision Metric"]

        %% Track 3: Objective Reward
        nReward["Reward Function"]
        nScoreReward["Constraints & Logic Compliance"]

        %% Aggregation
        nAggregator["Factor-Weighted Fusion Matrix"]
    end

    %% Output
    subgraph sOutput["Output Routing"]
        nFinal["FINAL EXACT SCORE (0.00-1.00)"]
    end

    %% Pathing
    nInput & nQuery --> nEmbed & nRerank & nReward
    
    nEmbed --> nScoreVector --> nAggregator
    nRerank --> nScorePrecise --> nAggregator
    nReward --> nScoreReward --> nAggregator
    
    nMeta --> nAggregator

    nAggregator --> nFinal
    nScoreObj -.->|Formats| nFinal

    %% Styling
    classDef t0 fill:#451A03,stroke:#F59E0B,stroke-width:1px,color:#fff
    classDef t1 fill:#14532D,stroke:#22C55E,stroke-width:2px,color:#fff
    classDef in fill:#1e293b,stroke:#475569,stroke-width:1px,color:#fff
    classDef out fill:#1E3A8A,stroke:#3B82F6,stroke-width:2px,color:#fff
    
    class sTier0,nScoreObj t0
    class sInput,nInput,nQuery,nMeta in
    class sTier1,nEmbed,nScoreVector,nRerank,nScorePrecise,nReward,nScoreReward,nAggregator t1
    class sOutput,nFinal out
```

## Key Mechanisms
1. **Semantic Evaluation (Cosine)**: Computes the basic underlying meaning gap between what the user asked and what the agent produced. If the user asked for a "Dog image" and got a "Cat image," the semantic score drops correctly.
2. **Precision Cross-Encoding**: Embedding algorithms are bad at precise negations. A Cross-Encoder reranks the results to catch exact matches. If a user says "I do NOT want a dog," ordinary embeddings fail the test, but the Reranker catches the strict semantic rejection.
3. **Reward Compliance Check**: Mechanically validates boolean logic requests ("Must be under 400 lines", "Must end in .py"). This is an instant pass/fail layer on the numeric score.
4. **Context Factor Aggregation**: Weights the above three scores based on metadata. E.g., if the user role is "Admin," the threshold for passing the reward function is higher.
