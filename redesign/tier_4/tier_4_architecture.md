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

## Function Registry

| Module | Function | Signature | Purpose |
|--------|----------|-----------|---------|
| `ooda_loop` | `run_ooda_loop` | `async (initial_state: AgentState) -> LoopResult` | Continuous OODA loop runner |
| `ooda_loop` | `run_ooda_cycle` | `async (state: AgentState) -> CycleResult` | Single Observe-Orient-Decide-Act cycle |
| `ooda_loop` | `observe` | `async (event_stream, short_term_memory) -> list[ObservationEvent]` | Phase 1: Sense environment events |
| `ooda_loop` | `orient` | `async (observations, rag_service, context_buffer) -> OrientedState` | Phase 2: Contextualize via RAG |
| `ooda_loop` | `decide` | `async (oriented_state, current_goals, graph_synthesizer) -> Decision` | Phase 3: Plan/replan via Tier 3 |
| `ooda_loop` | `act` | `async (decision, compiled_dag, mcp_host) -> ActionResult` | Phase 4: Execute DAG nodes via MCP |
| `async_multitasking` | `manage_async_tasks` | `async (node_result, dag_queue) -> NextAction` | Top-level async task manager |
| `async_multitasking` | `check_async_requirement` | `(node_result: ActionResult) -> bool` | Detect long-running tasks |
| `async_multitasking` | `park_dag_state` | `async (dag, short_term_memory) -> ParkingTicket` | Save DAG state to RAM queue |
| `async_multitasking` | `register_wait_listener` | `async (parking_ticket, event_type) -> WaitHandle` | Setup webhook/poll for completion |
| `async_multitasking` | `switch_context` | `async (dag_queue: DAGQueue) -> CompiledDAG \| None` | Load next priority DAG |
| `async_multitasking` | `request_deep_sleep` | `async (tier5_controller) -> SleepToken` | Signal Tier 5 for zero-compute sleep |
| `short_term_memory` | `update_dag_state` | `(dag_id, node_id, status) -> DagStateSnapshot` | Track DAG completion % |
| `short_term_memory` | `push_event` | `(event: ObservationEvent) -> None` | Add to LRU event cache |
| `short_term_memory` | `cache_entity` | `(key: str, value: Any, ttl: int \| None) -> None` | Store extracted entity temporarily |
| `short_term_memory` | `read_context` | `(query: str \| None) -> ContextSlice` | Read working memory context |
| `short_term_memory` | `flush_to_summarizer` | `() -> EpochSummary` | Compress and clear for Tier 5 commit |
| `short_term_memory` | `evict_stale_entries` | `(max_age_seconds: int) -> int` | LRU garbage collection |
