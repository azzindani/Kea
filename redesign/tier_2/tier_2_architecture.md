# Tier 2: Cognitive Engines (Intermediate Logic)

## Overview
Tier 2 serves as the strategic processing layer that combines basic primitives (from Tier 1) to derive more complex logical states. It manages the "what if" scenarios, exploratory analysis, and task-decomposition required by an autonomous agent.

**CRITICAL RULE**: Tier 2 depends heavily on Tiers 1 and 0, but remains oblivious to the existence of higher-level planners (Tier 3) or the OODA loop (Tier 4). It is purely a deterministic set of powerful functions that perform cognitive lifting.

## Scope & Responsibilities
- **Task Decomposition**: Takes a complex problem and breaks it down into sensible, actionable sub-tasks utilizing both syntactic parsing and semantic embedding constraints.
- **Curiosity Engine**: Evaluates unknown variables and creates investigative strategies to fill information gaps via the Knowledge base or MCP tools.
- **What-If Simulations**: Runs small-scale logic trees or counter-factual scenarios offline before handing a finalized recommendation up to Tier 3.

## Architecture

```mermaid
flowchart TD
    %% Base dependencies
    subgraph sTier1["Tier 1: Core Processing"]
        nT1["Classifiers & Extractors"]
    end

    %% T2 Scope
    subgraph sTier2["Tier 2: Cognitive Engines (`kernel/advanced/`)"]
        direction TB
        
        nDecomp["Task Decomposer"]
        nCuriosity["Curiosity Generator"]
        nSims["Simulation / What-If Modeler"]
        
        nDecomp -.-> nSims
        nCuriosity -.-> nSims
    end

    %% T3 Interface
    subgraph sTier3["Tier 3: Complex Orchestration"]
        direction TB
        nT3Engine["Planner & Node Synthesizer"]
    end
    
    %% Dependencies
    nT3Engine == "Aggregates" ==> sTier2
    sTier2 == "Calls Primitives" ==> sTier1
    
    classDef t1 fill:#14532D,stroke:#22C55E,stroke-width:1px,color:#fff
    classDef t2 fill:#064E3B,stroke:#10B981,stroke-width:2px,color:#fff
    classDef t3 fill:#1E3A8A,stroke:#3B82F6,stroke-width:1px,color:#fff
    
    class nT1,sTier1 t1
    class sTier2,nDecomp,nCuriosity,nSims t2
    class nT3Engine,sTier3 t3
```
