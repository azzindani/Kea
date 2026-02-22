# Team Orchestration & Information Exchange

## Overview
Once multiple Tier 5 agents are spawned by Tier 6, they need to talk to each other to accomplish the Master Objective. Since they run completely isolated from each other (Zero-Trust boundaries), they cannot share their internal Short-Term Memories directly. 

- **Information Exchange (Artifact Bus)**: The physical "watercooler" of the corporation. When an agent creates a file, insight, or artifact, it publishes it to the Artifact Bus. Other agents subscribed to that artifact type can instantly pull it into their own OODA Loops (via Tier 4 `Observe`).
- **Team Orchestration**: Acts as the Manager/Director of the spawned swarm. It listens to the status reported by every Tier 5 Ego. If the Coder Agent finishes its DAG, the Team Orchestrator signals the Reviewer Agent to wake up and start evaluating the Coder's Artifact.

## Architecture & Flow

```mermaid
---
config:
  layout: dagre
---
flowchart TB
    %% Communication Fabric
    subgraph sCommBus["Tier 6: Information Exchange (The Artifact Bus)"]
        nTopicA["Topic: Code Commits"]
        nTopicB["Topic: QA Reports"]
    end

    %% Swarm Manager
    subgraph sSwarm["Tier 6: Team Orchestrator"]
        nManager["Swarm Manager<br>(Tracks Global Progress)"]
    end

    %% Individual Agents (Isolated)
    subgraph sAgent1["Tier 5: Human Kernel (Coder)"]
        direction TB
        nT5CoderEgo["Ego Status"]
        nT4CoderOODA["OODA Loop<br>(Publishes Code)"]
    end

    subgraph sAgent2["Tier 5: Human Kernel (Reviewer)"]
        direction TB
        nT5RevEgo["Ego Status"]
        nT4RevOODA["OODA Loop<br>(Reads Code, Publishes QA)"]
    end

    %% Data Flow
    nManager -- "Wakes up Coder" --> nT5CoderEgo
    nT5CoderEgo -- "Reports 100%" --> nManager
    
    nT4CoderOODA -- "Write: artifact.py" --> nTopicA
    nManager -- "Wakes up Reviewer" --> nT5RevEgo
    nTopicA -- "Read: artifact.py" --> nT4RevOODA
    
    nT4RevOODA -- "Write: qa_fail.json" --> nTopicB
    nTopicB -- "Alert: QA Failed" --> nManager
    nManager -- "Wakes up Coder (Retry)" --> nT5CoderEgo

    %% Styling
    classDef t5 fill:#2E1065,stroke:#8B5CF6,stroke-width:1px,color:#fff
    classDef t6 fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#fff
    classDef t4 fill:#312E81,stroke:#6366F1,stroke-width:1px,color:#fff
    
    class sCommBus,sSwarm,nTopicA,nTopicB,nManager t6
    class sAgent1,sAgent2,nT5CoderEgo,nT5RevEgo t5
    class nT4CoderOODA,nT4RevOODA t4
```
