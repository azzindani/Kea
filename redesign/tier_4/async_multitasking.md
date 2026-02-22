# Asynchronous Multitasking (Waiting State)

## Overview
While Tier 5 handles the *concept* of going to sleep, **Tier 4 (The Execution Engine)** handles the complex reality of **Asynchronous Multitasking**. 

When the OODA loop fires an action (like "Train this ML model" or "Wait for a human to reply to this email"), it cannot just freeze and block the processing thread. The Execution Engine must be able to "park" the current DAG and pick up another active task, ensuring maximum efficiency.

## Architecture & Flow

```mermaid
---
config:
  layout: dagre
---
flowchart TB
    %% Interaction point
    subgraph sAct["Tier 4: OODA Act Phase"]
        nExecute["Execute Node"]
        nCheckAsync{"Is Task Async/Long-Running?"}
    end

    %% Tier 4 Multitasking Engine
    subgraph sTier4["Tier 4: Asynchronous Multitasking"]
        direction TB
        
        nParkDAG["Park Current DAG State<br>(Save to RAM)"]
        nWaitQueue["Waiting / Polling Queue<br>(Event Listeners)"]
        nContextSwitch["Context Switcher<br>(Load Next Priority DAG)"]
        
        nParkDAG --> nWaitQueue
        nParkDAG --> nContextSwitch
    end

    %% Connections
    subgraph sTier3["Tier 3 Planner"]
        nGetNewDAG["Request Next Workflow"]
    end
    
    subgraph sTier5["Tier 5 Ego"]
        nRequestSleep["Request Deep Sleep"]
    end

    %% Flow
    nExecute --> nCheckAsync
    nCheckAsync -- "Yes (Requires Wait)" --> nParkDAG
    
    nContextSwitch -- "Has other tasks?" --> nGetNewDAG
    nContextSwitch -- "No other tasks?" --> nRequestSleep
    
    nWaitQueue -- "Event Completes<br>(Webhook/Poll)" --> nContextSwitch

    %% Styling
    classDef t3 fill:#1E3A8A,stroke:#3B82F6,stroke-width:1px,color:#fff
    classDef t4 fill:#312E81,stroke:#6366F1,stroke-width:2px,color:#fff
    classDef t5 fill:#2E1065,stroke:#8B5CF6,stroke-width:1px,color:#fff
    
    class sAct,sTier4,nExecute,nCheckAsync,nParkDAG,nWaitQueue,nContextSwitch t4
    class sTier3,nGetNewDAG t3
    class sTier5,nRequestSleep t5
```

## Key Mechanisms
1. **DAG Parking**: If an MCP Tool returns a `Job ID` instead of a finished result, Tier 4 takes the entire current state of that DAG and "parks" it in the Short-Term Memory's `Waiting Queue`.
2. **Context Switching**: Tier 4 immediately asks Tier 3, "Do we have any other sub-tasks that can be executed in parallel right now?" If yes, it seamlessly swaps the context and begins executing the new DAG.
3. **Delegating to Tier 5**: If the `Waiting Queue` is full of parked tasks, but there is absolutely nothing else the agent can do *right now*, Tier 4 signals Tier 5. Tier 5 then safely puts the agent into a zero-compute `Deep Sleep` to preserve the Budget until an external webhook wakes it back up.
