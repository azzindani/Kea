# Lifecycle Controller (Autonomous Ego)

## Overview
The Lifecycle Controller represents Tier 5, the literal "Ego" or peak of the individual Human Kernel pyramid. Where the OODA loop (Tier 4) thinks in milliseconds and seconds, the Lifecycle Controller thinks in hours, days, and complete epochs. 

Its job is to define the agent's identity, hold its macro-objectives (the grand goal spanning across hundreds of OODA loops), and ensure the long-term memory of its existence is safely stored in the persistent Vault Data Center.

## Architecture & Flow

```mermaid
---
config:
  layout: dagre
---
flowchart TB
    %% The Corporate Overseer
    subgraph sCorp["Corporate Kernel (Tier 6+)"]
        nManager["Multi-Agent Orchestrator"]
    end

    %% Storage
    subgraph sVault["Vault (Data Center)"]
        direction TB
        nLongMem["Persistent Agent Memory"]
        nProfiles["Cognitive Profiles (Personas)"]
    end

    %% T5 Identity and Governance
    subgraph sT5["Tier 5: Autonomous Ego"]
        direction TB
        
        nSpawner["Agent Genesis / Initialization"]
        nEgo["Identity & Constraints Context"]
        nMacroGoal["Macro-Objective Tracker"]
        nSleepWake["Sleep / Wake / Panic Controller"]
        nCommit["Memory Commit Engine (End of Epoch)"]
        
        nSpawner --> nEgo
        nSpawner --> nMacroGoal
        nEgo --> nSleepWake
        nMacroGoal --> nCommit
    end

    %% T4 The Worker
    subgraph sT4["Tier 4: Execution Engine"]
        nOODA["The OODA Loop"]
    end

    %% Routing
    nManager -- "Spawn Agent (Task X)" --> nSpawner
    nProfiles -- "Load Profile" --> nSpawner
    
    nSleepWake -- "Start / Pause / Terminate" --> nOODA
    nMacroGoal -- "Passes Prime Directive" --> nOODA
    nOODA -- "Reports Massive Failure" --> nSleepWake
    
    nCommit -- "Persist Finalized Context" --> nLongMem

    %% Styling
    classDef t4 fill:#312E81,stroke:#6366F1,stroke-width:1px,color:#fff
    classDef t5 fill:#2E1065,stroke:#8B5CF6,stroke-width:2px,color:#fff
    classDef corp fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#fff
    classDef ext fill:#525252,stroke:#A3A3A3,stroke-width:1px,color:#fff
    
    class sVault,nLongMem,nProfiles ext
    class sCorp,nManager corp
    class sT5,nSpawner,nEgo,nMacroGoal,nSleepWake,nCommit t5
    class sT4,nOODA t4
```

## Key Mechanisms
1. **Sleep / Wake / Panic Control**: If Tier 4's OODA loop determines that the MCP Host is completely unreachable, it bubbles an alert up to Tier 5. Tier 5 issues a `Panic` state and puts the OODA loop into a `Deep Sleep`, checking the network only every 10 minutes to save computational resources. If the Corporate Kernel messages the agent to shut down, Tier 5 terminates the loops gracefully.
2. **Epoch Committing**: Instead of saving every single thought to the Vault DB (which would overwhelm the database), Tier 5 waits until a major objective is completed (an Epoch). It then takes the Short-Term memory from Tier 4, summarizes it, and commits it *once* to long-term storage in the Vault, keeping the history optimized.
3. **Identity Rigidity**: Once the `Agent Genesis` loads a cognitive profile from the Vault (e.g., "You are a Senior Security Auditor"), Tier 5 enforces those boundaries downwards. Tier 4 is completely bound by the strict constraints the Ego dictates.
