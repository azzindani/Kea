# Agent Spawner & Task Router

## Overview
The gateway into Tier 6 for any massive enterprise objective.

- **Task Router**: When a user submits an objective too large for a single agent (like "Build a web app and deploy it"), the Router breaks the master objective down into domain-specific chunks.
- **Agent Spawner**: Evaluates the chunks and dynamically spawns Human Kernels (Tier 5 instances) to handle them. It loads the appropriate "Cognitive Profiles" from the Vault (e.g., spawning one Frontend Developer, one Backend Developer, and one DevOps Engineer).

## Architecture & Flow

```mermaid
---
config:
  layout: dagre
---
flowchart TB
    %% Input
    nMasterGoal["Master Corporate Objective"]

    %% T6 Routing & Spawning
    subgraph sSpawningEngine["Tier 6: Spawner & Router Engine"]
        direction TB
        
        nParse["Evaluate Objective Scale"]
        nRoute["Route Domains<br>(Split into Roles needed)"]
        
        nProfiles["Query Required Profiles<br>(From Vault Database)"]
        nHardwareCheck["Resource / Hardware Check<br>(Do we have RAM to spawn 3 agents?)"]
        
        nDeploy["Initialize Tier 5 Egos"]
        
        nParse --> nRoute
        nRoute --> nProfiles --> nHardwareCheck --> nDeploy
    end

    %% Outputs (Activating Lower Tiers)
    subgraph sT5["Tier 5 Outputs"]
        nEgo1["Ego Instance 1 (Role A)"]
        nEgo2["Ego Instance 2 (Role B)"]
    end

    %% Flow
    nMasterGoal --> nParse
    nDeploy == "Spawns" ==> nEgo1 & nEgo2

    %% Styling
    classDef t5 fill:#2E1065,stroke:#8B5CF6,stroke-width:1px,color:#fff
    classDef t6 fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#fff
    
    class sSpawningEngine,nParse,nRoute,nProfiles,nHardwareCheck,nDeploy t6
    class sT5,nEgo1,nEgo2 t5
```
