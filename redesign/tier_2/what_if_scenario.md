# What-If / Simulation Engine

## Overview
The What-If Engine is a Tier 2 Cognitive Module. It runs fast, offline counter-factual tree searches or local evaluations before a risky action is ever committed to the live environment by Tier 4. It attempts to predict outcomes based on current knowledge logic.

## Architecture & Flow

```mermaid
---
config:
  layout: dagre
---
flowchart TB
    %% Inputs
    subgraph sState["Current State"]
        nProposedAction["Proposed T3 Workflow/Action"]
        nKnowledge["Local Knowledge (World State)"]
    end

    %% T2 Processing Engine
    subgraph sEngine["Simulation Engine"]
        direction TB
        
        nBranchGen["Generate Output Branches (Success/Fail)"]
        nPredictCon["Predict Environmental Consequences"]
        nScoreRisk["Calculate Risk / Reward Ratio"]
        
        nBranchGen --> nPredictCon --> nScoreRisk
    end

    %% T1 Tooling
    subgraph sTier1["Tier 1 Analysis"]
        nScore["Urgency & Sentiment Scorer"]
    end

    %% T3 Hook
    subgraph sAction["Simulation Verdict"]
        nApprove["Approve Action"]
        nReject["Reject & Request Alternative"]
        nModify["Append Safeguards"]
    end

    %% Routing
    nProposedAction & nKnowledge --> nBranchGen
    nPredictCon --> nScore
    nScore --> nScoreRisk
    
    nScoreRisk -- "Risk Acceptable" --> nApprove
    nScoreRisk -- "Risk Too High" --> nReject
    nScoreRisk -- "Moderate Risk" --> nModify

    %% Styling
    classDef t1 fill:#14532D,stroke:#22C55E,stroke-width:1px,color:#fff
    classDef t2 fill:#064E3B,stroke:#10B981,stroke-width:2px,color:#fff
    classDef action fill:#1E3A8A,stroke:#3B82F6,stroke-width:2px,color:#fff
    
    class sTier1,nScore t1
    class nBranchGen,nPredictCon,nScoreRisk t2
    class nApprove,nReject,nModify action
```
