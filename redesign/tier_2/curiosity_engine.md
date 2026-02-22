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
    %% Inputs
    subgraph sInputs["Current State"]
        nTask["Active Sub-Task"]
        nKnowledge["Current Local Knowledge"]
    end

    %% T2 Processing Engine
    subgraph sEngine["Curiosity Engine"]
        direction TB
        
        nGapDetect["Detect Information Gaps"]
        nFormulate["Formulate Exploration Questions"]
        nStrategy["Select Exploration Strategy<br>(RAG, Web Search, FS Scan)"]
        
        nGapDetect --> nFormulate --> nStrategy
    end

    %% T1 Dependencies
    subgraph sTier1["Tier 1 Check"]
        nValidate["Validate Required vs Available Data"]
    end

    %% External Hook (Handled by T3/T4)
    subgraph sAction["Exploration Output"]
        nActionTask["Generate Actionable Information-Gathering Tasks"]
    end

    %% Routing
    nTask & nKnowledge --> nValidate
    nValidate -- "Data Missing" --> nGapDetect
    nValidate -- "Data Sufficient" --> nBypass["Bypass Curiosity (Proceed)"]
    
    nStrategy --> nActionTask

    %% Styling
    classDef t1 fill:#14532D,stroke:#22C55E,stroke-width:1px,color:#fff
    classDef t2 fill:#064E3B,stroke:#10B981,stroke-width:2px,color:#fff
    classDef out fill:#1E3A8A,stroke:#3B82F6,stroke-width:2px,color:#fff
    
    class sTier1,nValidate t1
    class nGapDetect,nFormulate,nStrategy t2
    class nActionTask out
```
