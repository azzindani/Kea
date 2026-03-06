# Kea Kernel

The cognitive core of every Kea agent. The kernel implements a **Layered Pyramid Architecture** — modeled after the Linux kernel's modular subsystem design — where each tier provides a strict interface boundary and lower tiers never depend on upper ones.

Every agent in the system, from an intern-equivalent to the CEO-equivalent, runs the **same kernel logic**. Behavior is dictated entirely by **Cognitive Profiles** loaded from `knowledge/` and settings from `shared/config.py`.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  Tier 9 — Corporate Gateway (CEO / Client Entry Point)  │
├─────────────────────────────────────────────────────────┤
│  Tier 8 — Corporation Kernel (Middle Management)        │
├─────────────────────────────────────────────────────────┤
│  Tier 7 — Human Kernel Apex (Conscious Observer)        │
├─────────────────────────────────────────────────────────┤
│  Tier 6 — Metacognitive Oversight                       │
├─────────────────────────────────────────────────────────┤
│  Tier 5 — Autonomous Ego (Lifecycle & Energy)           │
├─────────────────────────────────────────────────────────┤
│  Tier 4 — Execution Engine (OODA Loop + STM)            │
├─────────────────────────────────────────────────────────┤
│  Tier 3 — Complex Orchestration (DAG Compilation)       │
├─────────────────────────────────────────────────────────┤
│  Tier 2 — Cognitive Engines (Reasoning + Simulation)    │
├─────────────────────────────────────────────────────────┤
│  Tier 1 — Core Processing Primitives (Deterministic)    │
├─────────────────────────────────────────────────────────┤
│  Tier 0 — Foundation (shared/ — schemas, config, I/O)   │
└─────────────────────────────────────────────────────────┘
```

**Strict Dependency Rule**: Tier N modules may call Tier N-1 primitives. The reverse is **forbidden**. No tier imports from a tier above itself.

---

## Directory Structure

```
kernel/
├── __init__.py                    # Public API — exports all ~600+ classes/functions
│
├── classification/                # Tier 1
├── intent_sentiment_urgency/      # Tier 1
├── entity_recognition/            # Tier 1
├── validation/                    # Tier 1
├── scoring/                       # Tier 1
├── modality/                      # Tier 1
├── location_and_time/             # Tier 1
│
├── task_decomposition/            # Tier 2
├── curiosity_engine/              # Tier 2
├── what_if_scenario/              # Tier 2
├── attention_and_plausibility/    # Tier 2
│
├── graph_synthesizer/             # Tier 3
├── node_assembler/                # Tier 3
├── advanced_planning/             # Tier 3
├── reflection_and_guardrails/     # Tier 3
│
├── ooda_loop/                     # Tier 4
├── short_term_memory/             # Tier 4
├── async_multitasking/            # Tier 4
│
├── lifecycle_controller/          # Tier 5
├── energy_and_interrupts/         # Tier 5
│
├── self_model/                    # Tier 6
├── activation_router/             # Tier 6
├── cognitive_load_monitor/        # Tier 6
├── hallucination_monitor/         # Tier 6
├── confidence_calibrator/         # Tier 6
├── noise_gate/                    # Tier 6
│
├── conscious_observer/            # Tier 7 — Human Kernel entry point
│
├── workforce_manager/             # Tier 8
├── team_orchestrator/             # Tier 8
├── quality_resolver/              # Tier 8
│
└── corporate_gateway/             # Tier 9
```

Each module follows a consistent layout:
- `engine.py` — core logic
- `types.py` — Pydantic models
- `__init__.py` — public exports

---

## Tier Reference

### Tier 0 — Foundation (`shared/`)

Not part of the `kernel/` directory, but the base upon which all tiers depend.

| Component | Purpose |
|-----------|---------|
| `shared/schemas.py` | Pydantic models for all API I/O |
| `shared/config.py` | Centralized settings (no hardcoding) |
| `shared/standard_io/` | `Signal`, `Result`, `KernelError` contracts |
| `shared/logging/main.py` | Structured logging primitives |
| `shared/hardware/` | Hardware-adaptive execution config |

---

### Tier 1 — Core Processing Primitives

**Pattern**: Pure lexical rules and mathematical normalization — **no LLM calls**. All functions accept a `Signal` and return a `Result`.

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `classification` | 3-layer signal classification (Linguistic → Semantic → Hybrid merge) | `classify()`, `run_linguistic_analysis()`, `run_semantic_proximity()`, `merge_classification_layers()` |
| `intent_sentiment_urgency` | Parallel primitive scorers | `detect_intent()`, `analyze_sentiment()`, `score_urgency()`, `run_primitive_scorers()` |
| `entity_recognition` | Named entity extraction with schema validation | `extract_entities()` |
| `validation` | 4-gate cascade (Syntax → Structure → Types → Bounds), short-circuits on first failure | `validate()` |
| `scoring` | 3-track hybrid evaluation (Semantic + Precision + Reward) | `score()` |
| `modality` | Omni-modal ingestion demux (text / audio / image / video / doc) | `ingest()` |
| `location_and_time` | Spatiotemporal anchoring — resolves "where" and "when" | `anchor_spatiotemporal()` |

---

### Tier 2 — Cognitive Engines

**Pattern**: Calls Tier 1 primitives. Operates on higher-level task structures and produces intermediate reasoning outputs.

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `task_decomposition` | Goal → sub-tasks with dependency graphs; complexity analysis (ATOMIC → COMPOUND → MULTI_DOMAIN) | `decompose_goal()` |
| `curiosity_engine` | Knowledge gap detection and exploration routing | `explore_gaps()` |
| `what_if_scenario` | Counter-factual simulation — generates outcome branches, predicts consequences, yields `SimulationVerdict` | `simulate_outcomes()` |
| `attention_and_plausibility` | Attention filtering and sanity checking | `run_cognitive_filters()` |

---

### Tier 3 — Complex Orchestration

**Pattern**: Translates Tier 2 reasoning into concrete, executable `ExecutableDAG` objects. Bridges high-level planning and low-level action.

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `graph_synthesizer` | JIT DAG compilation from sub-tasks; maps `SubTaskItem[]` → `ExecutableNode[]` → `ExecutableDAG` | `synthesize_plan()`, `map_subtasks_to_nodes()`, `calculate_dependency_edges()`, `compile_dag()` |
| `node_assembler` | Executable DAG node factory — wraps nodes in standard I/O, injects telemetry, hooks validation | `assemble_node()`, `wrap_in_standard_io()`, `inject_telemetry()` |
| `advanced_planning` | Sequencing, tool binding, hypothesis generation, cost/speed/fidelity routing | `plan_advanced()`, `sequence_and_prioritize()`, `bind_tools()`, `generate_hypotheses()` |
| `reflection_and_guardrails` | Pre-execution conscience gates and post-execution critique/optimization | `run_pre_execution_check()`, `run_post_execution_reflection()`, `check_value_guardrails()` |

---

### Tier 4 — Execution Engine

**Pattern**: The beating heart of a single agent. The **OODA Loop** is non-blocking async — it never waits synchronously on slow LLM calls. All tool execution is dispatched and tracked via `async_multitasking`. **Short-Term Memory** is the working RAM for a single execution context.

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `ooda_loop` | Observe-Orient-Decide-Act continuous execution cycle | `run_ooda_loop()`, `run_ooda_cycle()`, `observe()`, `orient()`, `decide()`, `act()` |
| `short_term_memory` | Ephemeral RAM: DAG state, event history, entity cache | `update_dag_state()`, `push_event()`, `cache_entity()`, `read_context()`, `get_dag_snapshot()` |
| `async_multitasking` | DAG parking, context switching, deep sleep delegation | `manage_async_tasks()`, `park_dag_state()`, `switch_context()`, `request_deep_sleep()` |

**OODA Cycle Phases**:
1. **Observe** — Poll event stream; push events into STM (non-blocking)
2. **Orient** — Contextualize via RAG bridge + STM working memory
3. **Decide** — Plan/replan via Tier 3; yields `Decision` (CONTINUE / REPLAN / PARK / COMPLETE / SLEEP)
4. **Act** — Execute DAG nodes via MCP Host dispatch; actual execution is remote

---

### Tier 5 — Autonomous Ego

**Pattern**: Controls the macro-lifecycle. Issues sleep/wake/terminate signals to the Tier 4 OODA Loop. Tracks four cost dimensions: `API_TOKENS`, `COMPUTE_MS`, `DB_WRITES`, `NETWORK_CALLS`.

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `lifecycle_controller` | Agent genesis, identity loading, sleep/wake/panic, epoch memory commit | `run_lifecycle()`, `initialize_agent()`, `load_cognitive_profile()`, `set_identity_constraints()`, `control_sleep_wake()`, `commit_epoch_memory()` |
| `energy_and_interrupts` | Budget tracking, exhaustion detection, corporate interrupt handling | `track_budget()`, `check_budget_exhaustion()`, `handle_interrupt()`, `manage_lifecycle_state()` |

---

### Tier 6 — Metacognitive Oversight

**Pattern**: Watches the OODA Loop from above. Detects anomalies — hallucinations, overconfidence, cognitive loops, stalls — and dynamically adjusts pipeline routing.

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `self_model` | Agent's internal self-representation: capability maps, cognitive state, accuracy history | `run_self_model()`, `assess_capability()`, `update_cognitive_state()`, `detect_capability_gap()`, `refresh_capability_map()` |
| `activation_router` | Selective module activation for energy efficiency; classifies signals as TRIVIAL → CRITICAL | `compute_activation_map()`, `classify_signal_complexity()`, `select_pipeline()`, `check_decision_cache()` |
| `cognitive_load_monitor` | Load measurement; detects loops, stalls, oscillations, goal drift | `monitor_cognitive_load()`, `measure_load()`, `detect_loop()`, `detect_stall()`, `detect_oscillation()`, `recommend_action()` |
| `hallucination_monitor` | Claim extraction and epistemic grounding verification; grades claims as GROUNDED / INFERRED / FABRICATED | `verify_grounding()`, `classify_claims()`, `grade_claim()`, `trace_evidence_chain()` |
| `confidence_calibrator` | Domain-specific calibration curves; detects overconfidence and underconfidence | `run_confidence_calibration()`, `calibrate_confidence()`, `detect_overconfidence()`, `update_calibration_curve()` |
| `noise_gate` | Final quality checkpoint; multi-dimensional quality check before output leaves the kernel | `filter_output()`, `apply_quality_threshold()`, `generate_rejection_feedback()`, `check_retry_budget()` |

**Activation Router Pipeline Templates** (config-driven, pressure-adaptive):

| Complexity | Pipeline | Tiers Active |
|-----------|---------|--------------|
| `TRIVIAL` | `fast_path` | T1, T4 |
| `SIMPLE` | `standard_path` | T1, T4 |
| `MODERATE` | `enhanced_path` | T1, T2, T4 |
| `COMPLEX` | `full_path` | T1, T2, T3, T4 |
| `CRITICAL` | `emergency_path` | T1, T4, T5 |

Pressure adaptation: normal (<0.6) uses the optimal pipeline; moderate (0.6–0.8) downgrades one level; high (>0.8) downgrades two. `CRITICAL` signals are never downgraded.

---

### Tier 7 — Human Kernel Apex (`conscious_observer/`)

The sole top-level entry point for a single agent. Orchestrates Tiers 1–6 across three phases, with Cognitive Load Monitor interception after every OODA cycle.

```
Phase 1 — GATE-IN:   T5 agent genesis → T1 perception → T6 routing
Phase 2 — EXECUTE:   T2/T3/T4 pipeline (mode-selected) + T6 CLM per cycle
Phase 3 — GATE-OUT:  T6 grounding → confidence calibration → noise gate → retry
```

This mirrors end-to-end human cognition:
> "Can I handle this?" → "Which approach?" → "Do the work" → "Am I going in circles?" → "Does my answer hold up?" → "Say it"

**Key Functions**: `run_conscious_observer()`
**Output**: `ConsciousObserverResult` (mode, phase_completed, final_verdict)

> **Note**: Phase 2 uses `run_ooda_cycle()` in a controlled loop — **not** `run_ooda_loop()` — so that the Cognitive Load Monitor can intercept between every cycle and apply CONTINUE / SIMPLIFY / ESCALATE / ABORT decisions.

---

### Tier 8 — Corporation Kernel

Manages teams of Tier 7 Human Kernels. Tier 8 does not do the work itself — it allocates, coordinates, and reviews.

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `workforce_manager` | Specialist matching, performance evaluation, scaling decisions | `hire_team()`, `match_profiles()` |
| `team_orchestrator` | Sprint planning (topological grouping), multi-agent DAG building, sprint review | `run_sprint()`, `coordinate_agents()` |
| `quality_resolver` | Cross-agent conflict detection, resolution cascade, sprint auditing | `audit_artifacts()`, `resolve_conflicts()` |

---

### Tier 9 — Corporate Gateway (`corporate_gateway/`)

The apex entry point for external clients. The only tier that interfaces with humans directly. Determines execution scale (SOLO / TEAM / SWARM) and synthesizes final output.

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `corporate_gateway` | Intent classification, strategic assessment, response synthesis, interrupt handling | `classify_intent()`, `assess_strategy()`, `synthesize_response()`, `handle_interrupt_logic()` |

> **Note**: This module contains pure logic only. The service layer (HTTP API) lives in `services/corporate_gateway/`.

---

## Signal Flow

### Full Multi-Agent Request (Tier 9 → Tier 1 → Tier 9)

```
Client Request
  ↓ [Corporate Gateway — T9]  Gate-In: intent classification & strategy assignment
  ↓ [Corporate Ops — T8]      Construct Mission DAG, spawn team
   ├── [Human Kernel A — T7]  GATE-IN → EXECUTE → GATE-OUT
   │    ├─ T1: Perception (modality → classification → ISU → NER)
   │    ├─ T6: Activation routing
   │    ├─ T4: OODA Loop (cycles until completion or budget exhaustion)
   │    └─ T6: Grounding → Confidence → Noise Gate → FilteredOutput A
   └── [Human Kernel B — T7]
        └─ ... → FilteredOutput B
  ↓ [Corporate Ops — T8]      QualityResolver: audit A vs B, resolve conflicts
  ↓ [Corporate Gateway — T9]  Gate-Out: executive synthesis
  → Response to Client
```

### Single-Agent Signal Pipeline (Tier 1 → Tier 7)

```
RawInput
  ↓ modality.ingest()                      [T1] — demux by type
  ↓ classification.classify()              [T1] — linguistic + semantic merge
  ↓ intent_sentiment_urgency.run_*()       [T1] — parallel label scoring
  ↓ entity_recognition.extract_entities()  [T1]
  ↓ activation_router.compute_activation_map()  [T6] — select pipeline
  ↓ task_decomposition.decompose_goal()    [T2]
  ↓ graph_synthesizer.synthesize_plan()    [T3] — compile ExecutableDAG
  ↓ ooda_loop.run_ooda_loop()              [T4] — execute until done
  ↓ noise_gate.filter_output()             [T6] — final quality gate
  → FilteredOutput
```

### DAG Lifecycle (Tier 3 → Tier 4)

```
1. T2: decompose_goal(WorldState) → list[SubTaskItem]
2. T3: synthesize_plan(SubTaskItem[]) → ExecutableDAG
3. T3: plan_advanced(SubTaskItem[], constraints) → TrackedPlan
4. T4: run_ooda_cycle(state, stm, active_dag) → CycleResult
5.     if Decision.action == REPLAN → feedback to T3 for replanning
```

---

## Key Data Structures

### Standard I/O Contract

All public functions accept `Signal` objects and return `Result` envelopes. Errors are **first-class data**, not exceptions.

```python
# Input
Signal(payload=..., source=..., trace_id=...)

# Output
Result(
    signals: list[Signal],     # successful outputs
    error: KernelError | None, # first-class error data
    metrics: ProcessingMetrics,
)
```

### Selected Type Inventory

| Tier | Key Types |
|------|-----------|
| T1 | `ClassificationResult`, `CognitiveLabels`, `ValidatedEntity`, `NumericScore` |
| T2 | `SubTaskItem` (with `depends_on`, `required_skills`, `required_tools`, `parallelizable`), `SimulationVerdict`, `WorldState` |
| T3 | `ExecutableDAG`, `ExecutableNode`, `Edge` (SEQUENTIAL / PARALLEL / CONDITIONAL), `ActionInstruction` |
| T4 | `AgentState`, `Decision` (CONTINUE / REPLAN / PARK / COMPLETE / SLEEP), `LoopResult`, `ShortTermMemory` |
| T5 | `AgentIdentity`, `CognitiveProfile`, `LifecycleSignal`, `BudgetState`, `InterruptSignal` |
| T6 | `CapabilityAssessment`, `ActivationMap`, `CognitiveLoad`, `GroundingReport`, `CalibratedConfidence` |
| T7 | `ConsciousObserverResult`, `ObserverExecutionResult` |
| T8 | `TeamSprintResult`, `QualityAudit`, `MissionChunk` |
| T9 | `CorporateGateInResult`, `CorporateProcessResponse` |

---

## Integration Protocol

| Concern | Rule |
|---------|------|
| **Config** | All settings from `shared.config.get_settings().kernel` — no hardcoding |
| **Logging** | All modules use `get_logger(__name__)` from `shared/logging/main.py` with context binding |
| **Errors** | Errors are `KernelError` (first-class data in `Result`), not raised exceptions |
| **Async** | All I/O is `async/await`; `time.sleep()` and blocking calls are forbidden in Tier 4 |
| **Tier isolation** | Tier N calls Tier N-1 only; no reverse dependencies |
| **Persistence** | Ephemeral state lives in `ShortTermMemory` (Tier 4); durable state persists to Vault via Lifecycle Controller (Tier 5) |
| **Tool execution** | Nodes are dispatched to `MCP Host` service; the kernel only tracks lifecycle, not execution internals |

---

## Design Principles

- **No monolithic KernelCell** — the kernel is a modular, composable toolkit. Each tier's output is the next tier's input.
- **Determinism at the base** — Tier 1 uses no LLMs; it provides fast, reliable primitives.
- **LLM as fallback** — Upper tiers use LLMs only when symbolic layers are insufficient.
- **Metacognition is built-in** — Tier 6 continuously monitors Tier 4, detecting hallucinations, load anomalies, and confidence drift without external intervention.
- **Config-driven behavior** — All thresholds, cycle limits, and routing rules are in `shared/config.py`. Changing agent behavior never requires code changes.
- **Hardware-adaptive** — No hardcoded worker counts or batch sizes. All resource allocation flows through `shared/hardware/`.
