# Intent, Sentiment, & Urgency (Primitives)

## Overview
Based on Kea's Layered Pyramid Architecture, **Intent Detection, Sentiment Analysis, and Urgency/Priority** are fundamental text-in/label-out classifiers. Because they do not require complex multi-step reasoning or tool use, they are strictly **Tier 1 Core Primitives**. 

Tier 2 and Tier 3 rely heavily on these fast, deterministic primitives to make higher-level cognitive decisions. Kea does not need to spin up a complex DAG to figure out if the user is angry; it runs a sub-100ms Tier 1 primitive to inject `Urgency: HIGH` into the state context.

## Architecture & Flow

```mermaid
---
config:
  layout: dagre
---
flowchart TB
    %% DOWNSTREAM T0 IMPORTS
    subgraph sTier0["Tier 0 Foundations"]
        direction LR
        nNormalize["Math Normalizer (normalization.md)"]
        nSchema["Label Output Schema"]
    end

    %% Inputs
    subgraph sInput["Raw Input Stream"]
        nInput["User Prompt / Event Data"]
    end

    %% T1 Processors
    subgraph sTier1["Tier 1: Scoring Primitives"]
        direction TB
        
        nIntent["Intent Detector<br>(What is the goal?)"]
        nSentiment["Sentiment Analyzer<br>(What is the emotional state?)"]
        nUrgency["Urgency & Priority Scorer<br>(How fast must we act?)"]
    end

    %% Output
    subgraph sHigher["Output to Higher Tiers"]
        nOut["Structured Cognitive Labels"]
    end

    %% Routing
    nInput --> nIntent & nSentiment & nUrgency
    nIntent & nSentiment & nUrgency -.->|Calculates via| nNormalize
    nNormalize -.->|Formats to| nSchema
    nSchema --> nOut

    %% Styling
    classDef t0 fill:#451A03,stroke:#F59E0B,stroke-width:1px,color:#fff
    classDef t1 fill:#14532D,stroke:#22C55E,stroke-width:2px,color:#fff
    classDef in fill:#1e293b,stroke:#475569,stroke-width:1px,color:#fff
    classDef out fill:#1E3A8A,stroke:#3B82F6,stroke-width:2px,color:#fff
    
    class sTier0,nNormalize,nSchema t0
    class sInput,nInput in
    class sTier1,nIntent,nSentiment,nUrgency t1
    class sHigher,nOut out
```

## Key Mechanisms
1. **Mathematical Grounding**: The text strings evaluated by these three engines do not return raw text back to the agent. They return probability scores. The Tier 0 Math Normalizer ensures the "Anger" sentiment score uses proper Min/Max logic before handing it off.
2. **Speed & Determinism**: Uses either small SLMs (like a very fast distilled BERT model) or pure lexical rule sets depending on context. The objective is to flag the input within milliseconds, creating an immediate context anchor for Tier 4 to observe.
