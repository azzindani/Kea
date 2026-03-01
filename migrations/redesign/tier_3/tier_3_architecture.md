# Tier 3: Complex Orchestration (Planner & Workflow Builder)

## Overview
Tier 3 represents the dynamic graph-building and orchestrating capabilities of the Human Kernel. Think of it as an internal "n8n" or LangGraph workflow generator. It dynamically maps out exactly how an agent will achieve its complex objectives.

**CRITICAL RULE**: Tier 3 utilizes the Cognitive Engines from Tier 2 and maps them as nodes in a directed graph. It generates executable plans. It does not control *when* these sequences are executed (that is the job of Tier 4).

## Scope & Responsibilities
- **Dynamic Workflow Builder**: Acts as the JIT (Just-In-Time) compiler for DAGs, dictating what executes sequentially and what runs in parallel.
- **Node Assembly**: Assembles specific behaviors, tools, and Tier 2 engines into discrete, executable LangGraph state nodes.
- **Dependency Resolution**: Ensures chronological steps have their necessary inputs satisfied by preceding outputs.

## Architecture

```mermaid
flowchart TD
    %% Base dependencies
    subgraph sTier2["Tier 2: Cognitive Engines"]
        nT2["Curiosity & Decomposition"]
    end
    subgraph sTier1["Tier 1: Core Processing"]
        nT1["Primitives"]
    end

    %% T3 Scope
    subgraph sTier3["Tier 3: Complex Orchestration (`orchestrator/`)"]
        direction TB
        
        nPlanner["Strategic Planner"]
        nDAGGen["DAG / Workflow Synthesizer"]
        nNodeGen["Node Assembler"]
        
        nPlanner --> nDAGGen
        nPlanner --> nNodeGen
        nNodeGen --> nDAGGen
    end

    %% T4 Interface
    subgraph sTier4["Tier 4: Execution Engine"]
        direction TB
        nT4Engine["The OODA Loop"]
    end
    
    %% Dependencies
    nT4Engine == "Executes the DAG" ==> sTier3
    sTier3 == "Calls & Resolves" ==> sTier2
    sTier3 -.-> "Direct Primitive Calls" -.-> sTier1
    
    classDef t1 fill:#14532D,stroke:#22C55E,stroke-width:1px,color:#fff
    classDef t2 fill:#064E3B,stroke:#10B981,stroke-width:1px,color:#fff
    classDef t3 fill:#1E3A8A,stroke:#3B82F6,stroke-width:2px,color:#fff
    classDef t4 fill:#312E81,stroke:#6366F1,stroke-width:1px,color:#fff
    
    class nT1,sTier1 t1
    class nT2,sTier2 t2
    class sTier3,nPlanner,nDAGGen,nNodeGen t3
    class nT4Engine,sTier4 t4
```

## Function Registry

| Module | Function | Signature | Purpose |
|--------|----------|-----------|---------|
| `graph_synthesizer` | `synthesize_plan` | `async (objective: str, state: AgentState) -> CompiledDAG` | Top-level DAG synthesis |
| `graph_synthesizer` | `map_subtasks_to_nodes` | `(subtasks: list[SubTaskItem]) -> list[ExecutableNode]` | Convert sub-tasks to graph nodes |
| `graph_synthesizer` | `calculate_dependency_edges` | `(nodes: list[ExecutableNode]) -> list[Edge]` | Determine sequential vs parallel edges |
| `graph_synthesizer` | `compile_dag` | `(nodes, edges) -> CompiledDAG` | Assemble LangGraph state machine |
| `graph_synthesizer` | `review_dag_with_simulation` | `async (dag: CompiledDAG) -> SimulationVerdict` | What-if dry-run validation |
| `node_assembler` | `assemble_node` | `(instruction, input_schema, output_schema) -> StateNodeFunction` | Top-level node factory |
| `node_assembler` | `wrap_in_standard_io` | `(action_callable: Callable) -> WrappedCallable` | Try/except + ErrorResponse wrapping |
| `node_assembler` | `inject_telemetry` | `(wrapped_callable, trace_id: str) -> InstrumentedCallable` | OpenTelemetry + structlog injection |
| `node_assembler` | `hook_input_validation` | `(callable, input_schema) -> ValidatedCallable` | Pre-execution Pydantic gate |
| `node_assembler` | `hook_output_validation` | `(callable, output_schema) -> StateNodeFunction` | Post-execution Pydantic gate |
| `advanced_planning` | `plan_advanced` | `async (subtasks, constraints) -> TrackedPlan` | Top-level advanced planning |
| `advanced_planning` | `sequence_and_prioritize` | `(subtasks, constraints) -> list[SequencedTask]` | Cost/speed/fidelity routing |
| `advanced_planning` | `bind_tools` | `async (sequenced_tasks, mcp_registry) -> list[BoundTask]` | MCP tool selection and binding |
| `advanced_planning` | `generate_hypotheses` | `(bound_tasks) -> list[ExpectedOutcome]` | Expected output schema generation |
| `advanced_planning` | `inject_progress_tracker` | `(tasks, hypotheses) -> TrackedPlan` | Attach progress tracking state |
| `reflection_and_guardrails` | `run_pre_execution_check` | `async (dag: CompiledDAG) -> ApprovalResult` | Pre-execution conscience gate |
| `reflection_and_guardrails` | `evaluate_consensus` | `async (dag_candidates) -> CompiledDAG` | Multi-path weighted voting |
| `reflection_and_guardrails` | `check_value_guardrails` | `(dag: CompiledDAG) -> GuardrailResult` | Ethics/security/corporate policy gate |
| `reflection_and_guardrails` | `run_post_execution_reflection` | `async (result, expected) -> ReflectionInsight` | Post-execution optimization |
| `reflection_and_guardrails` | `critique_execution` | `(result, expected) -> CritiqueReport` | Compare actual vs expected outcomes |
| `reflection_and_guardrails` | `optimize_loop` | `(critique: CritiqueReport) -> OptimizationSuggestion` | Generate improvement suggestions |
| `reflection_and_guardrails` | `commit_policy_update` | `async (suggestion) -> ReflectionInsight` | Persist lessons to long-term memory |
