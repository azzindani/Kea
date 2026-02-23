# Task Decomposition Engine

## Overview
The Task Decomposition Engine is a Tier 2 Cognitive Module. It takes a high-level goal, breaks it down down into sequential and parallel subtasks, and outputs a structured node graph that the Tier 3 Orchestrator can turn into an actionable DAG.

## Architecture & Flow

```mermaid
---
config:
  layout: dagre
---
flowchart TB
    %% DOWNSTREAM TIER 0 IMPORTS (SCHEMAS)
    subgraph sTier0["Tier 0: Universal Schemas (shared/schemas.py)"]
        direction LR
        nSchemaGoal["Base Model: Goal"]
        nSchemaTask["Base Model: SubTaskItem"]
    end

    %% DOWNSTREAM TIER 1 IMPORTS (PRIMITIVES)
    subgraph sTier1["Tier 1: Cognitive Primitives"]
        direction LR
        nIntent["PrimitiveScorers.detect_intent()<br>(intent_sentiment_urgency.md)"]
        nEntity["EntityRecognizer.extract_entities()<br>(entity_recognition.md)"]
    end

    %% Inputs
    subgraph sInputs["Current Agent Context"]
        nContext["Working World State"]
    end

    %% T2 Processing Engine
    subgraph sEngine["Tier 2: Task Decomposition Layer"]
        direction TB
        
        nAnalyze["1. Analyze Goal Complexity"]
        nSplit["2. Split into Logical Sub-Goals"]
        nDepCheck["3. Build Task Dependency Array"]
        nResourceCheck["4. Map Required Agent Skills"]
        
        nAnalyze --> nSplit --> nDepCheck --> nResourceCheck
    end

    %% Outputs
    subgraph sOutputs["Output to Orchestrator (Tier 3)"]
        nTaskList["Structured Array<br>[SubTaskItem, SubTaskItem]"]
    end

    %% Execution & Routing
    nSchemaGoal -.->|Parsed By| nIntent & nEntity
    nSchemaTask -.->|Formats| nTaskList

    nContext --> nAnalyze
    nIntent & nEntity -->|Signal Output| nAnalyze
    
    nResourceCheck --> nTaskList

    %% Styling
    classDef t0 fill:#451A03,stroke:#F59E0B,stroke-width:1px,color:#fff
    classDef t1 fill:#14532D,stroke:#22C55E,stroke-width:2px,color:#fff
    classDef t2 fill:#064E3B,stroke:#10B981,stroke-width:3px,color:#fff
    classDef out fill:#1E3A8A,stroke:#3B82F6,stroke-width:2px,color:#fff
    
    class sTier0,nSchemaGoal,nSchemaTask t0
    class sTier1,nIntent,nEntity t1
    class sEngine,nAnalyze,nSplit,nDepCheck,nResourceCheck t2
    class sOutputs,nTaskList out
```

## Function Decomposition

### `decompose_goal`
- **Signature**: `async decompose_goal(context: WorldState) -> list[SubTaskItem]`
- **Description**: Top-level orchestrator. Takes the current agent world state (containing the high-level goal), runs complexity analysis, splits into sub-goals, builds the dependency array, and maps required skills. Returns a structured list of `SubTaskItem` objects ready for the Tier 3 Graph Synthesizer to assemble into an executable DAG.
- **Calls**: `analyze_goal_complexity()`, `split_into_sub_goals()`, `build_dependency_array()`, `map_required_skills()`.

### `analyze_goal_complexity`
- **Signature**: `async analyze_goal_complexity(context: WorldState, intent: IntentLabel, entities: list[ValidatedEntity]) -> ComplexityAssessment`
- **Description**: Step 1. Evaluates the complexity of the high-level goal by examining the intent (from Tier 1 `detect_intent()`), the number and types of extracted entities, and the breadth of the world state context. Produces a `ComplexityAssessment` that categorizes the goal (atomic, compound, multi-domain) and estimates the number of sub-tasks needed.
- **Calls**: Tier 1 `intent_sentiment_urgency.detect_intent()`, Tier 1 `entity_recognition.extract_entities()`.

### `split_into_sub_goals`
- **Signature**: `split_into_sub_goals(assessment: ComplexityAssessment) -> list[SubGoal]`
- **Description**: Step 2. Decomposes the assessed goal into logical sub-goals. Atomic goals produce a single sub-goal. Compound goals are split along natural semantic boundaries (e.g., "build and deploy" becomes two sub-goals). Multi-domain goals are split by domain expertise (frontend, backend, infrastructure).
- **Calls**: None (pure logic based on assessment).

### `build_dependency_array`
- **Signature**: `build_dependency_array(sub_goals: list[SubGoal]) -> DependencyGraph`
- **Description**: Step 3. Analyzes input/output relationships between sub-goals to determine execution ordering. Identifies which sub-goals can run in parallel (no data dependencies) and which must run sequentially (output of one feeds input of another). Returns a directed graph of dependencies.
- **Calls**: None (topological sort algorithm).

### `map_required_skills`
- **Signature**: `map_required_skills(sub_goals: list[SubGoal], dependency_graph: DependencyGraph) -> list[SubTaskItem]`
- **Description**: Step 4. Annotates each sub-goal with the agent skills, tool categories, and knowledge domains required to execute it. Maps sub-goals to `SubTaskItem` schema objects with dependency edges, skill requirements, and estimated resource needs. This output directly feeds the Tier 3 Graph Synthesizer.
- **Calls**: Skill registry lookup from `knowledge/` profiles.
