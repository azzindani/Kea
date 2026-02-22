# Tier 4: Execution Engine (The OODA Loop)

## Overview
Tier 4 is the relentless engine that interfaces Kea with its simulated "world." It strictly relies on the Observe, Orient, Decide, and Act (OODA) loop. This component drives the flow of time for an agent, rapidly processing events, adjusting plans upon failure, and interacting with its environment.

**CRITICAL RULE**: The OODA loop controls the pacing, but it assumes the *content* of actions is determined by the Plan (Tier 3) and that the raw interpretation of events is handled by Primitives (Tier 1).

## Scope & Responsibilities
- **The Cognitive Cycle**: Runs continuous loops:
    1. Observe (Listen to environment, MCP tools, artifacts).
    2. Orient (Re-evaluate context, context engineering via RAG).
    3. Decide (Request a new plan or modify existing via Tier 3 DAGBuilder).
    4. Act (Execute a node from the DAG).
- **Short-Term Memory**: Holds an ephemeral memory space specifically to track the history of the current loop, enabling fast learning from immediate successes or failures.
- **Fault-Tolerance**: Implements safe fallback sleep cycles if tools or data sources abruptly go offline.

## Architecture

```mermaid
flowchart TD
    %% Tool & Memory Constraints
    subgraph sWorld["Environment & Services"]
        nMCP["MCP Host (Tools)"]
        nRAG["RAG Service (Knowledge)"]
        nLocalMem["Short-Term RAM"]
    end

    %% T4 Scope
    subgraph sTier4["Tier 4: Execution Engine"]
        direction TB
        
        nObserve["1. Observe (Sense)"]
        nOrient["2. Orient (Contextualize)"]
        nDecide["3. Decide (Plan)"]
        nAct["4. Act (Execute)"]
        
        nLocalMem <--> nObserve
        nObserve --> nOrient
        nOrient --> nDecide
        nDecide --> nAct
        nAct --> nObserve
    end

    %% Dependencies
    subgraph sTier3["Tier 3: Dynamic Planner"]
        nT3["DAG Synthesizer"]
    end
    subgraph sTier5["Tier 5: Autonomous Ego"]
        nT5["Lifecycle Controller"]
    end
    
    nT5 == "Wakes/Sleeps" ==> sTier4
    nDecide == "Requests Plan" ==> sTier3
    sTier3 == "Returns Graph" ==> nAct
    nAct <--> nMCP
    nOrient <--> nRAG
    
    classDef t3 fill:#1E3A8A,stroke:#3B82F6,stroke-width:1px,color:#fff
    classDef t4 fill:#312E81,stroke:#6366F1,stroke-width:2px,color:#fff
    classDef t5 fill:#2E1065,stroke:#8B5CF6,stroke-width:1px,color:#fff
    
    class sWorld,nMCP,nRAG,nLocalMem fill:#525252,stroke:#A3A3A3,stroke-width:1px,color:#fff
    class sTier3,nT3 t3
    class sTier4,nObserve,nOrient,nDecide,nAct t4
    class sTier5,nT5 t5
```
