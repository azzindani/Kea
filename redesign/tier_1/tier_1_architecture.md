# Tier 1: Core Processing (Kernel Primitives)

## Overview
Tier 1 represents the fundamental cognitive and computational building blocks for the Human Kernel, located primarily within the `kernel/` directory. It defines pure programmatic processing units meant to be invoked by higher-order cognitive layers.

**CRITICAL RULE**: Tier 1 may ONLY import from Tier 0. It must remain stateless on its own, processing inputs and returning outputs cleanly.

## Scope & Responsibilities
- **Classification**: Text categorization, structural analysis, and basic semantic grouping.
- **Intention Detection**: Recognizing underlying goals or objectives within a given input stream.
- **Urgency Measurement**: Determining the priority/time-sensitivity of incoming information.
- **Entity Extraction**: Identifying and standardizing real-world objects, numbers, parameters, or entities in a text.
- **Validation**: Fundamental logical and type sanity-checks on parsed data.

## Architecture

```mermaid
flowchart TD
    %% Base dependencies
    subgraph sTier0["Tier 0: Base Foundation"]
        nT0["Schemas & Protocols"]
    end

    %% T1 Scope
    subgraph sTier1["Tier 1: Core Processing (`kernel/`)"]
        direction TB
        
        nClassifier["Classification Module"]
        nIntent["Intention Detector"]
        nUrgency["Urgency Scorer"]
        nEntity["Entity Recognizer (NER)"]
        nValidator["Primitive Validator"]
        
        nClassifier -.-> nValidator
        nEntity -.-> nValidator
    end

    %% T2 Interface
    subgraph sTier2["Tier 2: Cognitive Engines"]
        direction TB
        nT2Engine["Curiosity / What-If Engine"]
    end
    
    %% Dependencies
    nT2Engine == "Executes" ==> sTier1
    sTier1 == "Imports" ==> sTier0
    
    classDef t0 fill:#451A03,stroke:#F59E0B,stroke-width:1px,color:#fff
    classDef t1 fill:#14532D,stroke:#22C55E,stroke-width:2px,color:#fff
    classDef t2 fill:#064E3B,stroke:#10B981,stroke-width:1px,color:#fff
    
    class nT0,sTier0 t0
    class sTier1,nClassifier,nIntent,nUrgency,nEntity,nValidator t1
    class nT2Engine,sTier2 t2
```
