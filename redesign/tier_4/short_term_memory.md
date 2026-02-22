# Short-Term RAM & Loop Context

## Overview
Located firmly in **Tier 4 (The Execution Engine)**, the `Short-Term Memory` module is the active "RAM" of the Human Kernel's rapid OODA Loop. It acts as the context buffer holding immediate successes, failures, and observations from the environment so the agent does not repeat mistakes instantly.

**CRITICAL RULE**: Short-Term Memory is highly ephemeral. Once a major Task or Goal is completed, the contents of this RAM are summarized by the Tier 5 `Lifecycle Controller` and pushed into permanent storage in the Vault Data Center. The RAM is then wiped clean to prevent context window bloat on the next major cycle.

## Architecture & Flow

```mermaid
---
config:
  layout: dagre
---
flowchart TB
    %% Event Handlers
    subgraph sOODA["The OODA Loop"]
        nObserve["Observe (Event Polling)"]
        nOrient["Orient (RAG/World Alignment)"]
        nAct["Act (Execution Result)"]
    end

    %% Core Tier 4 Memory State
    subgraph sRAM["Tier 4: Working Context Buffer (RAM)"]
        direction TB
        
        nStateGraph["Current DAG State Tracker<br>(% Complete, Failed Nodes)"]
        nHistoryQueue["Fast LRU Event Sequence Cache<br>(Last N Actions)"]
        nWorkingEntities["Temporary Extracted Entity Cache<br>(Keys/Ids/Locations)"]
        
        nStateGraph <--> nHistoryQueue
        nHistoryQueue <--> nWorkingEntities
    end

    %% T5 Persistence
    subgraph sT5["Tier 5: Macro Controller"]
        nSummarizer["Epoch Committer / Summarizer"]
    end

    %% Routing Flow
    nObserve -- "Push Env Changes" --> nHistoryQueue
    nAct -- "Push Action Success/Fail" --> nStateGraph
    nOrient -- "Read Context" --> nWorkingEntities
    
    nStateGraph -- "Cycle Complete (Flush RAM)" --> nSummarizer

    %% Styling
    classDef mem fill:#0f172a,stroke:#475569,stroke-width:2px,color:#fff
    classDef ooda fill:#312E81,stroke:#6366F1,stroke-width:1px,color:#fff
    classDef t5 fill:#2E1065,stroke:#8B5CF6,stroke-width:2px,color:#fff
    
    class sRAM,nStateGraph,nHistoryQueue,nWorkingEntities mem
    class sOODA,nObserve,nOrient,nAct ooda
    class sT5,nSummarizer t5
```

## Key Mechanisms
1. **LRU Event Sequence**: The `HistoryQueue` operates on a Least-Recently-Used policy (or sliding window) to ensure the LLM's context window is never overwhelmed. Old events are dropped from Tier 4 RAM automatically, though they might be logged as background telemetry in Tier 0.
2. **Entity Caching**: The `Working Entities` block holds specific API IDs, paths, names, or values retrieved by `Observe` so they can be injected efficiently into subsequent actions without requiring the agent to constantly query the Vector DB for variables it *just* learned.
