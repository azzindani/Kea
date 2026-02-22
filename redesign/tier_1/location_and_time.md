# Spatiotemporal Anchoring (Location & Time)

## Overview
A specialized **Tier 1 Primitive** dedicated exclusively to resolving "Where" and "When". When a User requests an operation, terms like "yesterday," "recently," or "near me" are highly ambiguous. 

This engine acts as a pre-processor: it takes the raw input, anchors it to physical reality (the User's System Time or Geo Anchor), and outputs a strict math-compatible range or bounds file, which Tier 2 Cognitive Engines use to safely perform Curiosity Gap detection or Task Validation.

## Architecture & Flow

```mermaid
---
config:
  layout: dagre
---
flowchart TB
    %% TIER 0 IMPORTS
    subgraph sTier0["Tier 0: Universal Schemas"]
        direction LR
        nSchemaContext["Unified Spatiotemporal Schema"]
    end

    %% INPUTS
    subgraph sInput["Incoming Context / Event"]
        nTime["User System Time (Now Anchor)"]
        nGeo["User Geo Anchor"]
        nQuery["Raw Prompt / Instruction"]
    end

    %% TIER 1 CORE
    subgraph sTier1["Tier 1: Spatiotemporal Engine"]
        direction TB
        
        %% Extraction
        subgraph sExtract["1. Signal Extraction"]
            nExtractTime["Extract Temporal Signals<br>(Absolute, Relative, Range)"]
            nExtractGeo["Extract Spatial Signals<br>(Explicit location, Hints)"]
        end

        %% Resolution
        subgraph sResolve["2. Hierarchical Resolution"]
            nResolveTime["Anchor → Normalize Time Range"]
            nResolveGeo["Geo Mapping (City → Region → Global)"]
        end

        %% Adjustment
        subgraph sAdapt["3. Adaptive Adjustment"]
            nAdaptTime["Ambiguity Fix & Recency Splitting"]
            nAdaptGeo["Scope Widening / Narrowing"]
        end

        %% Fusion
        subgraph sFusion["4. Hybrid Fusion Core"]
            nFusion["Merge Vectors into Confidence Matrix"]
        end
    end

    %% OUTPUT
    subgraph sOutput["Output Downstream"]
        nUnified["Final Spatiotemporal Block Object"]
    end

    %% Pathing
    nTime --> nExtractTime
    nGeo --> nExtractGeo
    nQuery --> nExtractTime & nExtractGeo

    nExtractTime --> nResolveTime --> nAdaptTime --> nFusion
    nExtractGeo --> nResolveGeo --> nAdaptGeo --> nFusion

    nSchemaContext -.->|Formats| nUnified
    nFusion -.->|Packages| nUnified

    %% Styling
    classDef t0 fill:#451A03,stroke:#F59E0B,stroke-width:1px,color:#fff
    classDef t1 fill:#14532D,stroke:#22C55E,stroke-width:2px,color:#fff
    classDef in fill:#1e293b,stroke:#475569,stroke-width:1px,color:#fff
    classDef out fill:#1E3A8A,stroke:#3B82F6,stroke-width:2px,color:#fff
    
    class sTier0,nSchemaContext t0
    class sInput,nTime,nGeo,nQuery in
    class sTier1,sExtract,sResolve,sAdapt,sFusion,nExtractTime,nExtractGeo,nResolveTime,nResolveGeo,nAdaptTime,nAdaptGeo,nFusion t1
    class sOutput,nUnified out
```

## Key Mechanisms
1. **Hierarchical Resolution**: Converts implicit locations into bounding boxes. If a user asks for "Coffee in Soho," it pulls the geo anchor. Is the user in NY or London? It resolves "Soho" via the hierarchy to exact coordinates.
2. **Ambiguity & Recency Fixes**: If "Recently" is used, the Temporal Adjustment dynamically scopes "Recently" depending on the context. If the task is fetching emails, "recently" is 24 hours. If it's analyzing stock prices, "recently" might be minutes.
3. **Hybrid Fusion**: The final layer guarantees that the temporal bounds match the spatial bounds, scoring its confidence before outputting a rigid schema block.
