# Tier 6: The Corporate Kernel (Macro-Orchestrator)

## Overview
Sitting entirely above the individual Human Kernel (Tiers 0-5) is **Tier 6: The Corporate Kernel**. 

While Tier 5 represents the "Ego" of a single employee, Tier 6 represents the "Corporation" itself. It does not perform tasks directly. Instead, it manages the workforce. It is responsible for dynamically scaling the system, assembling teams of Human Kernels, routing tasks to the right specialists, and enforcing corporate-wide governance.

## Architecture & Flow

```mermaid
---
config:
  layout: dagre
---
flowchart TB
    %% External Triggers
    subgraph sWorld["External World"]
        nUserReq["Massive User Request / Enterprise Objective"]
        nSystemEvent["System-Wide Event (e.g. Daily Audit)"]
    end

    %% Tier 6: Corporate Kernel
    subgraph sTier6["Tier 6: The Corporate Kernel"]
        direction TB
        
        nRouter["Task Router<br>(Decomposes Enterprise Goal)"]
        nSpawner["Agent Spawner<br>(Allocates Resources)"]
        nOrchestrator["Team Orchestrator<br>(Manages Hierarchies)"]
        nCommBus["Information Exchange / Artifact Bus<br>(Corporate Watercooler)"]
        
        nRouter --> nSpawner
        nSpawner --> nOrchestrator
        nOrchestrator <--> nCommBus
    end

    %% Tier 5: Individual Agents
    subgraph sTier5["Tier 5: Human Kernels (The Workforce)"]
        direction LR
        nAgentA["Agent A<br>(Researcher Profile)"]
        nAgentB["Agent B<br>(Coder Profile)"]
        nAgentC["Agent C<br>(Reviewer Profile)"]
    end

    %% Routing Flow
    nUserReq & nSystemEvent --> nRouter
    
    nOrchestrator == "Assigns Objectives" ==> sTier5
    sTier5 == "Shares Artifacts / Messages" ==> nCommBus

    %% Styling
    classDef t5 fill:#2E1065,stroke:#8B5CF6,stroke-width:1px,color:#fff
    classDef t6 fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#fff
    classDef ext fill:#525252,stroke:#A3A3A3,stroke-width:1px,color:#fff
    
    class sWorld,nUserReq,nSystemEvent ext
    class sTier6,nRouter,nSpawner,nOrchestrator,nCommBus t6
    class sTier5,nAgentA,nAgentB,nAgentC t5
```
