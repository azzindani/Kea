## Comprehensive Kernel Exploration Report
Show less
I've completed a thorough exploration of the `/home/user/Kea/kernel/` directory. Here's what I found:
---
## 1. DIRECTORY STRUCTURE
The kernel contains **79 Python files** organized into **25 specialized modules**, each implementing a specific cognitive function. The directory structure follows the **Layered Pyramid Architecture** with 7 tiers:
```
/home/user/Kea/kernel/
├── __init__.py (comprehensive exports)
├── activation_router/       (Tier 6)
├── advanced_planning/       (Tier 3)
├── async_multitasking/      (Tier 4)
├── attention_and_plausibility/ (Tier 2)
├── classification/          (Tier 1)
├── cognitive_load_monitor/  (Tier 6)
├── confidence_calibrator/   (Tier 6)
├── curiosity_engine/        (Tier 2)
├── energy_and_interrupts/   (Tier 5)
├── entity_recognition/      (Tier 1)
├── graph_synthesizer/       (Tier 3)
├── hallucination_monitor/   (Tier 6)
├── intent_sentiment_urgency/ (Tier 1)
├── lifecycle_controller/    (Tier 5)
├── location_and_time/       (Tier 1)
├── modality/               (Tier 1)
├── node_assembler/         (Tier 3)
├── noise_gate/             (Tier 6)
├── ooda_loop/              (Tier 4)
├── reflection_and_guardrails/ (Tier 3)
├── scoring/                (Tier 1)
├── self_model/             (Tier 6)
├── short_term_memory/      (Tier 4)
├── task_decomposition/     (Tier 2)
├── validation/             (Tier 1)
└── what_if_scenario/       (Tier 2)
```
---
## 2. TIER BREAKDOWN
### **TIER 0: Base Foundation** (`shared/`)
- Models and schemas (Pydantic)
- Standard I/O contracts
- Configuration management
- Logging primitives
- Hardware detection
- Embedding models
### **TIER 1: Core Processing Primitives**
| Module | Purpose | Key Functions |
|--------|---------|----------------|
| **classification** | 3-layer signal classification (Linguistic → Semantic → Hybrid) | `classify()`, `run_linguistic_analysis()`, `run_semantic_proximity()`, `merge_classification_layers()` |
| **intent_sentiment_urgency** | Parallel primitive scorers for cognitive labels | `detect_intent()`, `analyze_sentiment()`, `score_urgency()`, `run_primitive_scorers()` |
| **entity_recognition** | Named entity extraction with schema validation | `extract_entities()` |
| **validation** | 4-gate validation cascade (Syntax→Structure→Types→Bounds) | `validate()` - short-circuits on first failure |
| **scoring** | 3-track hybrid evaluation (Semantic+Precision+Reward) | `score()` |
| **modality** | Omni-modal ingestion (text/audio/image/video/doc) | `ingest()`, demuxes inputs by modality |
| **location_and_time** | Spatiotemporal anchoring | `anchor_spatiotemporal()` |
**Pattern**: All Tier 1 functions use **lexical rules** and **mathematical normalization** — no LLM calls. They return `Result` objects with structured signals.
---
### **TIER 2: Cognitive Engines**
| Module | Purpose | Key Functions |
|--------|---------|----------------|
| **task_decomposition** | Goal → Sub-task decomposition with dependency graphs | `decompose_goal()` - analyzes complexity (ATOMIC→COMPOUND→MULTI_DOMAIN), splits into sub-goals, builds topological sort, maps skills/tools |
| **curiosity_engine** | Knowledge gap detection and exploration routing | `explore_gaps()` |
| **what_if_scenario** | Offline counter-factual simulation and risk/reward analysis | `simulate_outcomes()` - generates outcome branches, predicts consequences, calculates verdict |
| **attention_and_plausibility** | Attention filtering and sanity checking | `run_cognitive_filters()` |
**Pattern**: Tier 2 modules call Tier 1 primitives. They operate on higher-level task structures and produce intermediate reasoning outputs.
---
### **TIER 3: Complex Orchestration**
| Module | Purpose | Key Functions |
|--------|---------|----------------|
| **graph_synthesizer** | JIT DAG compilation from sub-tasks | `synthesize_plan()`, `map_subtasks_to_nodes()`, `calculate_dependency_edges()`, `compile_dag()` - translates SubTaskItems → ExecutableNodes → ExecutableDAG |
| **node_assembler** | Executable DAG node factory with validation layers | `assemble_node()`, `wrap_in_standard_io()`, `inject_telemetry()`, `hook_input_validation()`, `hook_output_validation()` |
| **advanced_planning** | Sequencing, tool binding, hypothesis generation, progress tracking | `plan_advanced()`, `sequence_and_prioritize()`, `bind_tools()`, `generate_hypotheses()`, `inject_progress_tracker()` - implements cost/speed/fidelity routing |
| **reflection_and_guardrails** | Pre-execution conscience gates and post-execution optimization | `run_pre_execution_check()`, `run_post_execution_reflection()`, `check_value_guardrails()`, `critique_execution()` |
**Pattern**: Tier 3 orchestrates Tier 2 outputs into concrete execution plans (ExecutableDAG). It bridges high-level reasoning and low-level action.
---
### **TIER 4: Execution Engine**
| Module | Purpose | Key Functions |
|--------|---------|----------------|
| **ooda_loop** | Observe-Orient-Decide-Act continuous execution cycle (THE BEATING HEART) | `run_ooda_loop()`, `run_ooda_cycle()`, `observe()`, `orient()`, `decide()`, `act()` - rapid non-blocking iteration |
| **short_term_memory** | Ephemeral RAM for DAG state, event history, entity caching | `ShortTermMemory` class with methods: `update_dag_state()`, `push_event()`, `cache_entity()`, `read_context()`, `get_dag_snapshot()` |
| **async_multitasking** | DAG parking, context switching, deep sleep delegation | `manage_async_tasks()`, `check_async_requirement()`, `park_dag_state()`, `switch_context()`, `request_deep_sleep()` |
**Cycle Phases**:
1. **Observe**: Poll event stream, push to STM (non-blocking)
2. **Orient**: Contextualize via RAG + STM working memory
3. **Decide**: Plan/replan via Tier 3 based on oriented state
4. **Act**: Execute DAG nodes via MCP (dispatch to MCP Host)
**Pattern**: OODA Loop is **non-blocking async**. It never waits on slow LLM calls. STM tracks state between cycles.
---
### **TIER 5: Autonomous Ego**
| Module | Purpose | Key Functions |
|--------|---------|----------------|
| **lifecycle_controller** | Agent genesis, identity, sleep/wake/panic, epoch memory | `run_lifecycle()`, `initialize_agent()`, `load_cognitive_profile()`, `set_identity_constraints()`, `track_macro_objective()`, `control_sleep_wake()`, `commit_epoch_memory()` |
| **energy_and_interrupts** | Budget tracking, exhaustion detection, corporate interrupts | `track_budget()`, `check_budget_exhaustion()`, `check_budget_warning()`, `handle_interrupt()`, `manage_lifecycle_state()`, `enforce_energy_authority()` |
**Pattern**: Tier 5 controls the macro-lifecycle. It issues sleep/wake/terminate signals to Tier 4 OODA Loop. Tracks 4 cost dimensions: API_TOKENS, COMPUTE_MS, DB_WRITES, NETWORK_CALLS.
---
### **TIER 6: Conscious Observer (Metacognitive Oversight)**
| Module | Purpose | Key Functions |
|--------|---------|----------------|
| **self_model** | Agent's internal representation: capability assessment, cognitive state tracking, accuracy history, calibration history | `run_self_model()`, `assess_capability()`, `get_current_state()`, `update_cognitive_state()`, `update_accuracy_history()`, `get_calibration_history()`, `detect_capability_gap()`, `refresh_capability_map()` |
| **activation_router** | Selective module activation for energy conservation | `compute_activation_map()`, `classify_signal_complexity()`, `select_pipeline()`, `check_decision_cache()`, `cache_decision()` - classifies signals as TRIVIAL→CRITICAL, applies pressure-based downgrade |
| **cognitive_load_monitor** | Load measurement, loop/stall/oscillation/drift detection | `monitor_cognitive_load()`, `measure_load()`, `detect_loop()`, `detect_stall()`, `detect_oscillation()`, `detect_goal_drift()`, `recommend_action()` |
| **hallucination_monitor** | Claim extraction and epistemic grounding verification | `verify_grounding()`, `classify_claims()`, `grade_claim()`, `calculate_grounding_score()`, `trace_evidence_chain()` - grades claims as GROUNDED/INFERRED/FABRICATED |
| **confidence_calibrator** | Accuracy-confidence alignment for domain-specific calibration curves | `run_confidence_calibration()`, `calibrate_confidence()`, `detect_overconfidence()`, `detect_underconfidence()`, `update_calibration_curve()`, `get_calibration_curve()` |
| **noise_gate** | Final quality checkpoint before output leaves kernel | `filter_output()`, `apply_quality_threshold()`, `annotate_output()`, `generate_rejection_feedback()`, `check_retry_budget()`, `clear_retry_budget()` - multi-dimensional quality check |
**Pattern**: Tier 6 is **metacognitive oversight**. It watches the OODA Loop, detects anomalies, and adjusts pipeline routing dynamically.
---
## 3. KEY CLASSES & DATA STRUCTURES
### Core Data Flow Objects
**Standard I/O Pattern** (Tier 0):
```
Signal (input) → Result {signals[], error?, metrics} (output)
```
### Tier 1 Output Types
- `ClassificationResult` / `FallbackTrigger`
- `CognitiveLabels` (IntentLabel, SentimentLabel, UrgencyLabel)
- `ValidatedEntity`
- `SuccessResult` / `ErrorResponse`
- `NumericScore`
### Tier 2 Output Types
- `SubTaskItem` (with `depends_on`, `required_skills`, `required_tools`, `parallelizable`)
- `WorldState` (context, goal, knowledge_domains)
- `SimulationVerdict` (decision: PROCEED/DEFER/ESCALATE)
- `OutcomeBranch` (is_success, likelihood, consequences)
### Tier 3 Output Types
- `ExecutableNode` (node_id, instruction, input_keys, output_keys, tool_binding, status)
- `ExecutableDAG` (nodes[], edges[], entry/terminal_ids, parallel_groups, execution_order)
- `Edge` (from/to_node_id, kind: SEQUENTIAL/PARALLEL/CONDITIONAL)
- `ActionInstruction` (task_id, description, action_type, parameters)
### Tier 4 Output Types
- `AgentState` (agent_id, status, current_objectives, active_dag_id, cycle_count, total_cost)
- `Decision` (action: CONTINUE/REPLAN/PARK/COMPLETE/SLEEP, reasoning, target_node_ids)
- `OrientedState` (is_blocked, blocking_reason, enriched_context, observation_summary)
- `CycleResult` (cycle_number, next_action, action_results, artifacts_produced)
- `LoopResult` (agent_id, total_cycles, termination_reason, final_state, objectives_completed)
- `ObservationEvent` (description, source: SYSTEM/MCP_TOOL/USER, payload)
### Tier 4 Memory (ShortTermMemory)
```python
class ShortTermMemory:
    _dag_states: dict[dag_id → dict[node_id → NodeExecutionStatus]]
    _event_history: OrderedDict[event_id → ObservationEvent]  (LRU, max=config)
    _entity_cache: OrderedDict[key → CachedEntity]  (TTL-based)
    
Methods:
    update_dag_state(dag_id, node_id, status) → DagStateSnapshot
    push_event(ObservationEvent) → None
    cache_entity(key, value) → None
    read_context(kit) → ContextSlice
    get_dag_snapshot(dag_id) → DagStateSnapshot
```
### Tier 5 Output Types
- `AgentIdentity` (agent_id, role, profile_id, created_utc)
- `CognitiveProfile` (skills[], tools[], knowledge_domains[], constraints[])
- `LifecycleSignal` (type: GENESIS/ACTIVATE/SLEEP/PANIC/TERMINATE)
- `BudgetState` (total_tokens_consumed, total_cost_consumed, utilization, token_limit, cost_limit)
- `InterruptSignal` (type: KILL/OVERRIDE/GRANT, source, action)
### Tier 6 Output Types
- `CapabilityAssessment` (can_handle, confidence, gap, partial_capabilities)
- `ActivationMap` (active_modules{module→bool}, complexity_level, selected_pipeline)
- `CognitiveLoad` (compute_load, time_load, breadth_load, total)
- `GroundingReport` (claims[], grounding_score, verdict)
- `CalibratedConfidence` (stated, calibrated, grounding_score)
---
## 4. EXISTING ORCHESTRATION & COORDINATION PATTERNS
### **Inter-Tier Communication**
**Strict Dependency Flow** (Lower → Upper only):
```
Tier 0 ← Tier 1 ← Tier 2 ← Tier 3 ← Tier 4 ← Tier 5 ← Tier 6
```
**Never Reverse**: Tier N modules NEVER import from Tier N+1.
### **Main Orchestration Entry Points**
**The OODA Loop (Tier 4)** is the primary orchestrator:
```python
async def run_ooda_loop(
    initial_state: AgentState,
    stm: ShortTermMemory | None = None,
    active_dag: ExecutableDAG | None = None,
    kit: InferenceKit | None = None,
) → Result
```
**Loop Flow**:
1. For each cycle (up to `config.ooda_max_cycles`):
   - `observe()` → collect events into STM
   - `orient()` → contextualize with RAG + STM
   - `decide()` → pick action (CONTINUE/REPLAN/PARK/COMPLETE/SLEEP)
   - `act()` → execute DAG nodes
   - Check lifecycle signals from Tier 5
2. Return `LoopResult` with artifacts and termination reason
### **DAG Lifecycle** (Tier 3 → Tier 4)
1. **Tier 2**: `decompose_goal(WorldState)` → list[SubTaskItem]
2. **Tier 3**: `synthesize_plan(SubTaskItem[])` → ExecutableDAG
3. **Tier 3**: `plan_advanced(SubTaskItem[], constraints)` → TrackedPlan
4. **Tier 4**: `run_ooda_cycle(state, stm, active_dag)` → CycleResult
5. If `Decision.action == REPLAN`: feedback to Tier 3 for replanning
### **Signal Processing Pipeline** (Tier 1 → Tier 6)
Typical signal flow:
```
RawInput
  ↓ [Modality]
  ↓ [Classification] → ClassificationResult
  ↓ [Intent/Sentiment/Urgency] → CognitiveLabels
  ↓ [Entity Recognition] → ValidatedEntity[]
  ↓ [Activation Router (T6)] → ActivationMap (select pipeline)
  ↓ [Task Decomposition (T2)] → SubTaskItem[]
  ↓ [Graph Synthesizer (T3)] → ExecutableDAG
  ↓ [OODA Loop (T4)] → CycleResult/LoopResult
  ↓ [Self Model + Hallucination Monitor (T6)] → GroundingReport
  ↓ [Confidence Calibrator (T6)] → CalibratedConfidence
  ↓ [Noise Gate (T6)] → FilteredOutput or RejectedOutput
```
### **Async/Blocking Guarantees**
**CRITICAL RULE**: Tier 4 OODA Loop must NEVER block synchronously on slow calls:
- All LLM calls in classification/decomposition are `async`
- Actual tool execution (MCP calls) are dispatched and tracked via `async_multitasking`
- Node execution returns immediately with `job_id`; polling happens in next cycle
---
## 5. KernelCell CLASS (if exists)
**There is NO explicit `KernelCell` class.** Instead, the kernel uses a **distributed, tier-based architecture** where:
- Each tier is a **specialized cognitive processor**
- **Tier 1-6 modules are "the cells"** — each implements a specific cognitive function
- The **OODA Loop (Tier 4)** acts as the **central coordination hub**
- **Short-Term Memory (Tier 4)** acts as the **working RAM** for a single agent
- **Lifecycle Controller (Tier 5)** manages **agent identity and lifecycle state**
The `__init__.py` file exports all ~600+ classes and functions, making the kernel a **pluggable cognitive toolkit** rather than a monolithic cell.
---
## 6. HOW TIERS CALL EACH OTHER
### **Calling Convention**
All public functions follow this pattern:
```python
async def high_level_function(
    input_data: Signal | Model,
    kit: InferenceKit | None = None,
) -> Result:
    """
    Accept Signal/Pydantic models.
    Return Result {signals[], error, metrics}.
    """
    ref = _ref("function_name")  # ModuleRef(tier, module, function)
    start = time.perf_counter()
    
    try:
        # Call lower-tier primitives
        result_tier_n_minus_1 = await tier_n_minus_1_function(...)
        
        # Aggregate/orchestrate
        output = process(result_tier_n_minus_1)
        
        # Wrap in Result
        signal = create_data_signal(data=output.model_dump(), ...)
        return ok(signals=[signal], metrics=metrics)
    except Exception as exc:
        return fail(error=processing_error(...), metrics=metrics)
```
### **Examples of Real Call Chains**
**Chain 1: Task Decomposition**
```
task_decomposition.decompose_goal()
  ├─ intent_sentiment_urgency.detect_intent()  [T1]
  ├─ entity_recognition.extract_entities()     [T1]
  └─ [LLM fallback for advanced decomposition]
```
**Chain 2: Graph Synthesis**
```
graph_synthesizer.synthesize_plan()
  ├─ task_decomposition.decompose_goal()        [T2]
  ├─ map_subtasks_to_nodes()
  │  └─ [LLM inference for action_type]
  ├─ calculate_dependency_edges()
  └─ what_if_scenario.simulate_outcomes()       [T2]
```
**Chain 3: OODA Cycle**
```
ooda_loop.run_ooda_cycle()
  ├─ observe(event_stream, stm)
  ├─ orient(observations, stm, rag_context)
  │  └─ [Detect blocking conditions via simple heuristics or LLM]
  ├─ decide(oriented_state, objectives, active_dag, stm)
  │  └─ [Check DAG progress via STM snapshots]
  └─ act(decision, active_dag, stm)
     └─ [Execute nodes; actual execution delegated to Orchestrator service]
```
**Chain 4: Signal Processing (Full Pipeline)**
```
modality.ingest(raw_input)                      [T1]
  ↓ [if text]
classification.classify(text, profile_rules)   [T1]
  ├─ run_linguistic_analysis()
  ├─ run_semantic_proximity()  [async]
  └─ merge_classification_layers()
  ↓
intent_sentiment_urgency.run_primitive_scorers() [T1]
  ├─ detect_intent()
  ├─ analyze_sentiment()
  └─ score_urgency()
  ↓
entity_recognition.extract_entities()          [T1]
  ↓
activation_router.compute_activation_map()     [T6]
  ├─ classify_signal_complexity()
  ├─ select_pipeline()
  └─ cache_decision() [if repeated signal]
  ↓
[If proceeding...]
task_decomposition.decompose_goal()            [T2]
  ↓
graph_synthesizer.synthesize_plan()            [T3]
  ↓
ooda_loop.run_ooda_loop()                      [T4]
  └─ [cycles until completion]
```
---
## 7. CONFIGURATION & LOGGING
**Config (Tier 0)**:
All hardcoded settings live in `shared/config.py` via `get_settings().kernel`:
- `classification_confidence_threshold`
- `ooda_max_cycles`
- `stm_max_events`, `stm_max_entities`
- `planning_speed_weight`, `planning_cost_weight`, `planning_fidelity_weight`
- `noise_gate_grounding_threshold`
- etc.
**Logging (Tier 0)**:
All modules use `get_logger(__name__)` from `shared/logging/main.py`:
```python
log = get_logger(__name__)
log.info("message", key=value, duration_ms=elapsed)
log.warning("warning", error=str(exc))
log.error("error", ...)
```
---
## 8. KEY PATTERNS & PRINCIPLES
| Pattern | Implementation |
|---------|-----------------|
| **Tier Isolation** | Strict one-way dependencies (lower → upper only) |
| **Async-First** | All I/O is `async`; no `time.sleep()` in Tier 4 |
| **Standard I/O** | All public functions: `Signal → Result {signals[], error, metrics}` |
| **Config-Driven** | All settings in `shared/config.py`; no hardcoding |
| **Structured Logging** | All logging via `get_logger()` with context binding |
| **Error Handling** | Errors are **first-class data** in `Result`, not exceptions |
| **Modular Fallbacks** | LLM tie-breakers when symbolic layers are uncertain |
| **Ephemeral State** | STM holds per-cycle state; Tier 5 persists to Vault |
| **Metacognitive Loop** | Tier 6 watches Tier 4, detects anomalies, adjusts routing |
| **DAG Execution** | Nodes are dispatched to MCP Host; kernel only tracks lifecycle |
---
## 9. MODULE COUNT & FILE COUNT
- **25 modules** (one per cognitive function)
- **79 Python files** (engine.py, types.py, __init__.py per module)
- **~600+ exported classes/functions** in kernel/__init__.py
- **7 tiers** of coordination (Tier 0 being shared/)
---
## Summary
The Kea **Human Kernel** is a sophisticated, **fractal cognitive architecture** where:
1. **Tier 1** provides **fast, deterministic primitives** (no LLM dependency)
2. **Tier 2** performs **high-level reasoning** (decomposition, simulation)
3. **Tier 3** **compiles concrete execution plans** (DAGs)
4. **Tier 4** is the **beating heart** — the **OODA Loop** that iterates rapidly, non-blocking
5. **Tier 5** manages **agent lifecycle and resources**
6. **Tier 6** provides **metacognitive oversight** (load monitoring, hallucination detection, confidence calibration)
The **OODA Loop** (Tier 4) with **Short-Term Memory** is the central coordination hub. It calls down into Tier 3 for replanning, reads working state from STM, and receives macro-directives from Tier 5.
All **inter-module communication** uses Pydantic models and `Result` envelopes. **All configuration** is centralized in `shared/config.py`. **All logging** is structured and context-aware.
There is **no monolithic KernelCell** — instead, the kernel is a **modular, composable toolkit** where each tier's output is the next tier's input, forming a unified cognitive processing pipeline.
agentId: a4314a5b18b26e00c (for resuming to continue this agent's work if needed)
<usage>total_tokens: 73730
tool_uses: 24
duration_ms: 92039</usage>

---
## Comprehensive Kea Kernel Exploration Report
Show less
Based on my thorough analysis of the Kea codebase, here's a detailed breakdown of the architecture, Tier 6 modules, and how they can be orchestrated into a top-level system:
---
## **1. KERNEL STRUCTURE & EXPORT HIERARCHY**
### `/home/user/Kea/kernel/__init__.py` Summary
The kernel is architected as a **Layered Pyramid** with 6 Tiers, implementing a strict **Linux Kernel-style modular subsystem design**:
- **Tier 0**: Foundation (shared/schemas, config, standard_io)
- **Tier 1**: Core Processors (classification, intent/sentiment/urgency, entity recognition, validation, scoring, modality, location_and_time)
- **Tier 2**: Cognitive Engines (task decomposition, curiosity, what-if scenario, attention)
- **Tier 3**: Complex Orchestration (graph synthesizer, node assembler, advanced planning, reflection/guardrails)
- **Tier 4**: Execution Engine (OODA loop, async multitasking, short-term memory)
- **Tier 5**: Autonomous Ego (lifecycle controller, energy/interrupts)
- **Tier 6**: Conscious Observer (self model, activation router, cognitive load monitor, hallucination monitor, confidence calibrator, noise gate)
**Key Design Principle**: Lower tiers are never dependent on upper tiers. Information flows upward through the pyramid.
---
## **2. TIER 6 MODULES - DETAILED ANALYSIS**
### **Module 1: `self_model` (Tier 6)**
**Location**: `/home/user/Kea/kernel/self_model/engine.py`
**Purpose**: The agent's internal self-representation and capability assessment.
**Key Functions**:
- `assess_capability(signal_tags, identity, kit)` → `CapabilityAssessment`
- `get_current_state()` → `AgentCognitiveState`
- `update_cognitive_state(...)` → Updates processing phase, active modules, task description, cycle count
- `detect_capability_gap(signal_tags, identity, kit)` → `CapabilityGap | None`
- `refresh_capability_map(identity, available_tools, knowledge_domains)` → None
- `run_self_model(signal_tags, identity, kit)` → `Result`
**Key Type Structures**:
```python
SignalTags:  # From Tier 1
  - urgency, domain, complexity, source_type, intent
  - entity_count, required_skills, required_tools
CapabilityAssessment:
  - can_handle: bool
  - confidence: float (0.0-1.0)
  - gap: CapabilityGap | None
  - partial_capabilities: list[str]
AgentCognitiveState:
  - agent_id, processing_phase (IDLE/OBSERVE/PRE_EXECUTION/DURING_EXECUTION/POST_EXECUTION)
  - active_modules, current_task_description
  - ooda_cycle_count, elapsed_ms, current_dag_id
CalibrationHistory:
  - data_points: list[CalibrationDataPoint]
  - domain_accuracy: dict[str, float]
  - overall_accuracy, sample_count
```
**Integration**: Maintains module-level state (skills, tools, domains, constraints, calibration history).
---
### **Module 2: `activation_router` (Tier 6)**
**Location**: `/home/user/Kea/kernel/activation_router/engine.py`
**Purpose**: Selective module activation based on signal complexity and system pressure.
**Key Functions**:
- `classify_signal_complexity(signal_tags, kit)` → `ComplexityLevel`
- `select_pipeline(complexity, pressure)` → `PipelineConfig`
- `check_decision_cache(signal_tags)` → `ActivationMap | None`
- `cache_decision(signal_tags, activation_map)` → None
- `compute_activation_map(signal_tags, capability, pressure, kit)` → `Result`
**Pipeline Templates** (Config-driven):
```
TRIVIAL:    [T1, T4] → fast_path (greetings)
SIMPLE:     [T1, T4] → standard_path (direct questions)
MODERATE:   [T1, T2, T4] → enhanced_path (multi-step with tools)
COMPLEX:    [T1, T2, T3, T4] → full_path (strategy/analysis with DAG)
CRITICAL:   [T1, T4, T5] → emergency_path (system alerts)
```
**Pressure Adaptation**:
- Normal (<0.6): Use optimal pipeline
- Moderate (0.6-0.8): Downgrade 1 level
- High (>0.8): Downgrade 2 levels
- CRITICAL: Never downgrade
**Key Type Structures**:
```python
ComplexityLevel: TRIVIAL | SIMPLE | MODERATE | COMPLEX | CRITICAL
ModuleActivation: ACTIVE | DORMANT
ActivationMap:
  - pipeline: PipelineConfig
  - module_states: dict[str, ModuleActivation]
  - pressure_downgraded: bool
  - original_complexity: ComplexityLevel | None
  - cache_hit: bool
```
---
### **Module 3: `cognitive_load_monitor` (Tier 6)**
**Location**: `/home/user/Kea/kernel/cognitive_load_monitor/engine.py`
**Purpose**: Measure processing budget and detect anomalies (loops, stalls, oscillations, goal drift).
**Key Functions**:
- `measure_load(activation_map, telemetry)` → `CognitiveLoad`
- `detect_loop(recent_decisions)` → `LoopDetection`
- `detect_stall(cycle_duration, expected_duration)` → `bool`
- `detect_oscillation(recent_decisions)` → `OscillationDetection`
- `detect_goal_drift(recent_outputs, original_objective, kit)` → `GoalDriftDetection`
- `recommend_action(load, loops, stall, oscillation, drift)` → `LoadRecommendation`
- `monitor_cognitive_load(activation_map, telemetry, recent_decisions, ...)` → `Result`
**Load Dimensions** (Weighted aggregate):
- **Compute**: tokens + cycles vs budget
- **Time**: wall clock vs expected duration
- **Breadth**: active modules vs capacity
**Decision Ladder**:
- CONTINUE: load < 0.6, no anomalies
- SIMPLIFY: load 0.6-0.8 OR minor loop/oscillation/stall
- ESCALATE: load > 0.8 OR goal drift OR persistent loop
- ABORT: load > 0.95 OR unbreakable loop
**Key Type Structures**:
```python
CycleTelemetry:
  - cycle_number, tokens_consumed, cycle_duration_ms
  - expected_duration_ms, active_module_count
  - total_cycles_budget, total_tokens_budget
CognitiveLoad:
  - compute_load, time_load, breadth_load, aggregate (0.0-1.0)
LoadAction: CONTINUE | SIMPLIFY | ESCALATE | ABORT
LoadRecommendation:
  - action, reasoning
  - load_snapshot, loop/stall/oscillation/drift_detected
```
---
### **Module 4: `hallucination_monitor` (Tier 6)**
**Location**: `/home/user/Kea/kernel/hallucination_monitor/engine.py`
**Purpose**: Epistemic grounding verification—extract, classify, grade claims.
**Key Functions**:
- `classify_claims(output_text, kit)` → `list[Claim]`
- `grade_claim(claim, evidence, kit)` → `ClaimGrade`
- `calculate_grounding_score(grades)` → `float`
- `trace_evidence_chain(claim, evidence)` → `list[EvidenceLink]`
- `verify_grounding(output, evidence, kit)` → `Result`
**Claim Classification**:
- FACTUAL: Verifiable facts (needs direct evidence)
- REASONING: Logical derivations (needs reasoning chain)
- OPINION: Subjective statements (auto-grounded, labeled)
**Grading Levels**:
- GROUNDED: Direct evidence found (similarity ≥ threshold)
- INFERRED: Partially derivable from grounded claims
- FABRICATED: No supporting evidence
**Evidence Matching**: Keyword overlap heuristic at kernel level; service layer uses embeddings.
**Key Type Structures**:
```python
Claim:
  - claim_id, text, claim_type (FACTUAL|REASONING|OPINION)
  - source_sentence, position
ClaimGrade:
  - claim_id, grade (GROUNDED|INFERRED|FABRICATED)
  - evidence_links: list[EvidenceLink]
  - best_similarity, reasoning
GroundingReport:
  - output_id, total_claims, grounded/inferred/fabricated_count
  - claim_grades, grounding_score (0.0-1.0)
```
---
### **Module 5: `confidence_calibrator` (Tier 6)**
**Location**: `/home/user/Kea/kernel/confidence_calibrator/engine.py`
**Purpose**: Accuracy-confidence alignment via domain-specific calibration curves.
**Key Functions**:
- `calibrate_confidence(stated_confidence, grounding_score, history, domain)` → `CalibratedConfidence`
- `detect_overconfidence(stated, calibrated)` → `bool`
- `detect_underconfidence(stated, calibrated)` → `bool`
- `update_calibration_curve(predicted, actual_accuracy, domain)` → None
- `get_calibration_curve(domain)` → `CalibrationCurve`
- `run_confidence_calibration(stated_confidence, grounding_score, history, domain)` → `Result`
**Calibration Logic**:
- Looks up domain-specific curve
- Applies Platt-style correction from bin mapping
- Grounds result with hard upper bound from grounding score
- Formula: `calibrated = min(correction(stated), grounding_score)`
**Domain Curves**: Binned mapping of stated confidence → observed accuracy (0.1 increments).
**Key Type Structures**:
```python
CalibratedConfidence:
  - stated_confidence, calibrated_confidence
  - correction_factor (calibrated/stated ratio)
  - is_overconfident, is_underconfident
  - domain, warning (human-readable)
CalibrationCurve:
  - domain, bin_mapping (str → float)
  - sample_count, last_updated_utc
```
---
### **Module 6: `noise_gate` (Tier 6)**
**Location**: `/home/user/Kea/kernel/noise_gate/engine.py`
**Purpose**: Final quality checkpoint before output leaves kernel—multi-dimensional filtering.
**Key Functions**:
- `apply_quality_threshold(grounding_score, confidence, quality_bar_override)` → `bool`
- `annotate_output(output, grounding, confidence)` → `FilteredOutput`
- `generate_rejection_feedback(output, grounding, confidence)` → `RejectedOutput`
- `check_retry_budget(output_id)` → `RetryBudgetStatus`
- `clear_retry_budget(output_id)` → None
- `filter_output(output, grounding, confidence, quality_bar_override)` → `Result`
**Pass/Fail Criteria**:
- Grounding score ≥ threshold AND Confidence ≥ threshold
- Thresholds can be overridden by T5 identity constraints
**Rejection Feedback**:
- Failed dimensions (GROUNDING, CONFIDENCE, LOAD, MULTIPLE)
- Specific fabricated claim IDs
- Actionable suggestions
- Retry budget tracking (exhaustion triggers escalation)
**Key Type Structures**:
```python
ToolOutput:
  - output_id, content, metadata
  - source_node_id, source_dag_id
FilteredOutput (passed):
  - output_id, content, metadata
  - quality: QualityMetadata (grounding_score, calibrated_confidence, etc.)
  - passed: bool (True)
RejectedOutput (failed):
  - output_id, content
  - guidance: RetryGuidance
  - passed: bool (False)
RetryBudgetStatus:
  - output_id, retries_used, retries_remaining, should_escalate
```
---
## **3. INTEGRATION PATTERNS**
### **Standard Result Protocol**
All functions follow this contract:
```python
async def run_*_module(...) -> Result:
    # Returns:
    # - ok(signals=[signal], metrics=metrics) on success
    # - fail(error=error, metrics=metrics) on failure
```
### **Signal & Metrics**
```python
Signal: Contains module_ref, schema, data, origin, tags, trace_id
Metrics: duration_ms, module_ref
ModuleRef: tier (int), module (str), function (str)
```
### **Module Dependencies (Data Flow)**
```
T1 Classification/Intent/Urgency
  ↓
T6 Activation Router (uses SignalTags)
  ↓ provides ActivationMap
T4 OODA Loop (runs selected modules)
  ↓ produces Decision + ToolOutput
T6 Cognitive Load Monitor (consumes CycleTelemetry, Decisions)
  ↓ produces LoadRecommendation (CONTINUE/SIMPLIFY/ESCALATE/ABORT)
T6 Hallucination Monitor (consumes ToolOutput + Evidence)
  ↓ produces GroundingReport
T6 Confidence Calibrator (consumes grounding_score)
  ↓ produces CalibratedConfidence
T6 Noise Gate (consumes Grounding + Confidence)
  ↓ produces FilteredOutput or RejectedOutput
```
---
## **4. TIER 6 ORCHESTRATOR DESIGN PROPOSAL**
### **Architecture: A Top-Level Tier 6 Conscious Observer**
The Tier 6 modules naturally orchestrate into a **"Conscious Observer" metacognitive layer**:
```python
class Tier6Orchestrator:
    """
    Metacognitive oversight: coordinates all Tier 6 modules
    to provide holistic quality assurance and adaptive control.
    """
    
    async def run_full_t6_checkpoint(
        self,
        signal_tags: SignalTags,
        identity: IdentityContext,
        output: ToolOutput,
        evidence: list[Origin],
        activation_map: ActivationMap,
        telemetry: CycleTelemetry,
        recent_decisions: list[Decision],
        original_objective: str,
        kit: InferenceKit | None = None,
    ) -> T6CheckpointResult:
        """
        Execute full Tier 6 quality checkpoint pipeline:
        
        1. Self-Model: Assess capability, track state
        2. Activation Router: Decide which modules to activate
        3. Cognitive Load Monitor: Measure load, detect anomalies
        4. Hallucination Monitor: Grade claims, generate grounding report
        5. Confidence Calibrator: Calibrate stated confidence
        6. Noise Gate: Final quality gate + retry logic
        
        Returns: Structured decision on output quality + recommended action
        """
```
### **Sequential Pipeline Logic**
```
PHASE 1: PRE-EXECUTION ASSESSMENT
├─ Self-Model.assess_capability(signal_tags, identity)
│  └─ Determines: can_handle (bool), confidence, gaps
├─ Activation Router.compute_activation_map(signal_tags, capability, pressure)
│  └─ Determines: which modules activate for this signal
└─ Early Exit: If not capable, escalate to T5
PHASE 2: EXECUTION MONITORING (During OODA)
├─ Cognitive Load Monitor.monitor_cognitive_load(...)
│  ├─ measure_load(activation_map, telemetry)
│  ├─ detect_loop(recent_decisions)
│  ├─ detect_stall(cycle_duration, expected_duration)
│  ├─ detect_oscillation(recent_decisions)
│  ├─ detect_goal_drift(recent_outputs, original_objective)
│  └─ recommend_action(...) → LoadAction (CONTINUE/SIMPLIFY/ESCALATE/ABORT)
└─ Adaptive Response: If not CONTINUE, feed recommendation to T4
PHASE 3: POST-EXECUTION FILTERING (Before Output Release)
├─ Hallucination Monitor.verify_grounding(output, evidence)
│  └─ Produces: GroundingReport (per-claim grades, grounding_score)
├─ Confidence Calibrator.run_confidence_calibration(
│     stated_confidence, grounding_score, history, domain)
│  └─ Produces: CalibratedConfidence (with overconfidence detection)
└─ Noise Gate.filter_output(output, grounding, confidence)
   ├─ If passes: → FilteredOutput (annotated with quality metadata)
   └─ If fails: → RejectedOutput (with retry guidance)
```
### **Output Decision Types**
```python
@dataclass
class T6CheckpointResult:
    """Complete Tier 6 assessment result."""
    
    # Pre-execution decision
    capability_verdict: CapabilityAssessment
    activation_map: ActivationMap
    
    # Execution monitoring
    load_recommendation: LoadRecommendation
    load_action: LoadAction  # Direct recommendation
    
    # Post-execution filtering
    grounding_report: GroundingReport
    calibrated_confidence: CalibratedConfidence
    final_verdict: FilteredOutput | RejectedOutput
    
    # Metadata
    overall_quality_score: float  # Aggregate 0.0-1.0
    should_escalate_to_t5: bool
    should_retry: bool
    retry_guidance: RetryGuidance | None
```
---
## **5. SERVICES/ORCHESTRATOR INTEGRATION**
### **Current State**
- `/home/user/Kea/services/orchestrator/main.py` is a **FastAPI stub** in REDESIGN mode
- Currently only serves health checks and tool listing
- Execution endpoints throw `501 Not Implemented`
- Architecture shows intended flow: Gateway → Orchestrator → Kernel → MCP Host + Vault
### **Proposed Integration**
The Orchestrator service should:
1. **Receive request** from Gateway (ExecutionRequest)
2. **Initialize** T5 Lifecycle Controller for agent genesis
3. **Loop OODA Cycles** via T4:
   - For each cycle:
     - T1 classifies incoming signal
     - T6 Activation Router selects pipeline
     - T4 executes OODA cycle
     - T6 Cognitive Load Monitor checks for anomalies
     - If anomaly: escalate to T5 or abort
4. **Post-execute**: T6 Noise Gate filters output
5. **Return** FilteredOutput to Gateway
---
## **6. KEY FILE PATHS FOR REFERENCE**
| Component | Path |
|-----------|------|
| Kernel Init (All Exports) | `/home/user/Kea/kernel/__init__.py` |
| Self Model | `/home/user/Kea/kernel/self_model/engine.py`, `types.py` |
| Activation Router | `/home/user/Kea/kernel/activation_router/engine.py`, `types.py` |
| Cognitive Load Monitor | `/home/user/Kea/kernel/cognitive_load_monitor/engine.py`, `types.py` |
| Hallucination Monitor | `/home/user/Kea/kernel/hallucination_monitor/engine.py`, `types.py` |
| Confidence Calibrator | `/home/user/Kea/kernel/confidence_calibrator/engine.py`, `types.py` |
| Noise Gate | `/home/user/Kea/kernel/noise_gate/engine.py`, `types.py` |
| OODA Loop (T4) | `/home/user/Kea/kernel/ooda_loop/engine.py` |
| Lifecycle Controller (T5) | `/home/user/Kea/kernel/lifecycle_controller/engine.py` |
| Orchestrator Service | `/home/user/Kea/services/orchestrator/main.py` |
---
## **7. SUMMARY**
**Tier 6 ("Conscious Observer")** is a cohesive **metacognitive oversight layer** composed of 6 specialized engines:
1. **Self-Model**: Self-knowledge & capability assessment
2. **Activation Router**: Complexity → pipeline selection
3. **Cognitive Load Monitor**: Budget measurement + anomaly detection
4. **Hallucination Monitor**: Epistemic grounding verification
5. **Confidence Calibrator**: Accuracy-confidence alignment
6. **Noise Gate**: Final quality checkpoint + retry logic
All modules follow the same **Result protocol**, accept/return **Pydantic types**, and integrate seamlessly into a top-level **Tier 6 Orchestrator** that bridges T4/T5 execution with post-execution quality assurance.
The **services/orchestrator** is the **service-layer wrapper** that will invoke this kernel logic via HTTP-isolated microservices architecture.
agentId: a4d7b3e939c8ca798 (for resuming to continue this agent's work if needed)
<usage>total_tokens: 77487

---
## Exploration Report: Kea Codebase Analysis
Show less
### 1. Redesign Directory Status
**Status**: The `/home/user/Kea/redesign/` directory **does NOT exist**. The redesign specifications mentioned in `CLAUDE.md` are planned but not yet created in the filesystem.
### 2. Kernel-Related Settings in `/home/user/Kea/shared/config.py`
The `KernelSettings` class (lines 630-823) contains extensive configuration:
**OODA Settings (Tier 4)**:
```python
ooda_max_cycles: int = 100
ooda_poll_timeout_ms: float = 1000.0
ooda_tick_interval_ms: float = 50.0
ooda_blocked_retry_limit: int = 3
```
**Noise Gate Thresholds (Tier 6)**:
```python
noise_gate_grounding_threshold: float = 0.6
noise_gate_confidence_threshold: float = 0.5
noise_gate_max_retries: int = 3
```
**Activation Router Settings (Tier 6)**:
```python
activation_urgency_weight: float = 0.30
activation_structural_weight: float = 0.25
activation_domain_weight: float = 0.25
activation_gap_weight: float = 0.20
activation_cache_ttl_seconds: int = 30
activation_pressure_moderate: float = 0.6
activation_pressure_high: float = 0.8
```
**Cognitive Load Monitor Settings (Tier 6)**:
```python
load_compute_weight: float = 0.40
load_time_weight: float = 0.35
load_breadth_weight: float = 0.25
load_loop_detection_window: int = 10
load_loop_repeat_threshold: int = 3
load_stall_multiplier: float = 3.0
load_threshold_simplify: float = 0.6
load_threshold_escalate: float = 0.8
load_threshold_abort: float = 0.95
load_goal_drift_threshold: float = 0.4
```
**Budget/Energy Settings (Tier 5)**:
```python
budget_token_limit: int = 1_000_000
budget_cost_limit: float = 100.0
budget_epoch_token_limit: int = 200_000
budget_warning_threshold: float = 0.8
budget_exhaustion_threshold: float = 0.95
```
### 3. Exact Type Names from Kernel Files
#### `/home/user/Kea/kernel/lifecycle_controller/types.py`
**LifecycleSignal** (lines 131-136):
```python
class LifecycleSignal(BaseModel):
    signal_type: LifecycleSignalType
    reason: str
    payload: dict[str, Any]
```
**LifecycleSignalType** (lines 121-128):
```python
class LifecycleSignalType(StrEnum):
    START = "start"
    PAUSE = "pause"
    PANIC = "panic"
    TERMINATE = "terminate"
    RESUME = "resume"
```
**AgentIdentity** (lines 43-49):
```python
class AgentIdentity(BaseModel):
    agent_id: str
    role: str
    profile_id: str
    created_utc: str
```
**CognitiveProfile** (lines 57-88):
```python
class CognitiveProfile(BaseModel):
    profile_id: str
    role_name: str
    skills: list[str]
    tools_allowed: list[str]
    tools_forbidden: list[str]
    knowledge_domains: list[str]
    ethical_constraints: list[str]
    quality_bar: float
    max_parallel_tasks: int
```
#### `/home/user/Kea/kernel/ooda_loop/types.py`
**AgentState** (lines 43-61):
```python
class AgentState(BaseModel):
    agent_id: str
    status: AgentStatus
    current_objectives: list[MacroObjective]
    active_dag_id: str | None
    context: dict[str, Any]
    cycle_count: int
    total_cost: float
```
**Decision** (lines 136-152):
```python
class Decision(BaseModel):
    action: DecisionAction
    reasoning: str
    target_node_ids: list[str]
    replan_objective: str
    replan_context: dict[str, Any]
```
**CycleResult** (lines 200-213):
```python
class CycleResult(BaseModel):
    cycle_number: int
    next_action: CycleAction
    action_results: list[ActionResult]
    state_snapshot: dict[str, Any]
    artifacts_produced: list[str]
```
**LoopResult** (lines 226-239):
```python
class LoopResult(BaseModel):
    agent_id: str
    total_cycles: int
    termination_reason: LoopTerminationReason
    final_state: dict[str, Any]
    total_duration_ms: float
    total_cost: float
    objectives_completed: list[str]
    artifacts_produced: list[str]
```
**ObservationEvent** (lines 32-47):
```python
class ObservationEvent(BaseModel):
    event_id: str
    source: EventSource
    description: str
    payload: dict[str, Any]
    timestamp_utc: str
    priority: int
```
#### `/home/user/Kea/kernel/activation_router/types.py`
**ActivationMap** (lines 85-115):
```python
class ActivationMap(BaseModel):
    pipeline: PipelineConfig | None
    module_states: dict[str, ModuleActivation | ModuleState]
    required_tools: list[str]
    pressure_downgraded: bool
    original_complexity: ComplexityLevel | None
    cache_hit: bool
```
**PipelineConfig** (lines 64-77):
```python
class PipelineConfig(BaseModel):
    pipeline_name: str
    complexity_level: ComplexityLevel
    active_tiers: list[int]
    active_modules: list[str]
    description: str
```
**ComplexityLevel** (lines 19-26):
```python
class ComplexityLevel(StrEnum):
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"
```
**ModuleActivation** (lines 34-38):
```python
class ModuleActivation(StrEnum):
    ACTIVE = "active"
    DORMANT = "dormant"
```
### 4. Conscious Observer / Human Kernel Status
**No separate `kernel/conscious_observer/` module exists.** However, Tier 6 (Conscious Observer) is **fully implemented** across multiple dedicated modules:
1. **`kernel/self_model/`** — Capability assessment, cognitive state tracking
2. **`kernel/activation_router/`** — Module activation & pipeline selection
3. **`kernel/cognitive_load_monitor/`** — Load measurement & loop detection
4. **`kernel/hallucination_monitor/`** — Claim grading & evidence tracing
5. **`kernel/confidence_calibrator/`** — Calibration curves & confidence detection
6. **`kernel/noise_gate/`** — Quality filtering & rejection feedback
All Tier 6 exports are available in `/home/user/Kea/kernel/__init__.py` (lines 1-500+, comprehensive `__all__` list).
The architecture is described in the kernel docstring (lines 6-60 of `__init__.py`) as:
```
Tier 6: Conscious Observer (kernel/) → Self Model, Activation Router, Load Monitor,
                                       Hallucination Monitor, Confidence Calibrator, Noise Gate
```
---
### Summary Table of Key Types
| File | Type Name | Key Fields |
|------|-----------|-----------|
| `lifecycle_controller/types.py` | `LifecycleSignal` | `signal_type`, `reason`, `payload` |
| `lifecycle_controller/types.py` | `AgentIdentity` | `agent_id`, `role`, `profile_id`, `created_utc` |
| `lifecycle_controller/types.py` | `CognitiveProfile` | `profile_id`, `role_name`, `skills`, `tools_allowed`, `knowledge_domains`, `quality_bar` |
| `ooda_loop/types.py` | `AgentState` | `agent_id`, `status`, `current_objectives`, `active_dag_id`, `context`, `cycle_count` |
| `ooda_loop/types.py` | `Decision` | `action`, `reasoning`, `target_node_ids`, `replan_objective` |
| `ooda_loop/types.py` | `CycleResult` | `cycle_number`, `next_action`, `action_results`, `state_snapshot` |
| `ooda_loop/types.py` | `LoopResult` | `agent_id`, `total_cycles`, `termination_reason`, `final_state`, `objectives_completed` |
| `ooda_loop/types.py` | `ObservationEvent` | `event_id`, `source`, `description`, `payload`, `timestamp_utc`, `priority` |
| `activation_router/types.py` | `ActivationMap` | `pipeline`, `module_states`, `required_tools`, `pressure_downgraded` |
| `activation_router/types.py` | `PipelineConfig` | `pipeline_name`, `complexity_level`, `active_tiers`, `active_modules` |
| `activation_router/types.py` | `ComplexityLevel` | `TRIVIAL`, `SIMPLE`, `MODERATE`, `COMPLEX`, `CRITICAL` |
Human Kernel (Tier 1-6) is fully implemented across 27 kernel submodules, with no missing "conscious_observer" directory needed.
agentId: afb14b24ac1a89858 (for resuming to continue this agent's work if needed)
<usage>total_tokens: 48107

---
# Plan: Tier 6 `ConsciousObserver` Orchestrator
 
## Context
 
The Human Kernel has 6 fully-implemented Tier 6 modules (self_model, activation_router, cognitive_load_monitor, hallucination_monitor, confidence_calibrator, noise_gate) but no top-level orchestrator that ties them together. As a result, there is no single entry point that processes any input end-to-end like a human does. This plan creates a `ConsciousObserver` orchestrator in `redesign/` that:
 
1. Accepts **any input modality** (text/audio/image/video/doc)
2. Routes it through the right cognitive pipeline using T6 oversight
3. Monitors execution in real-time and adapts (simplify/escalate/abort)
4. Applies a quality gate to all outputs before releasing them
 
This mimics human cognition: **assess capability → route attention → think → monitor load → review before speaking**.
 
---
 
## Architecture: Three Phases + Four Pipeline Modes
 
### High-Level Flow
 
```
RawInput (any modality)
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  PHASE 1: GATE-IN (T1 Perception + T6 Routing)      │
│  T1: ingest → classify → ISU scorers → entities     │
│  T6: activation_router → activation_map             │
│  T6: self_model → capability check                  │
│   ├─ not capable → Escalate to T5 immediately       │
│   └─ capable → determine ProcessingMode             │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│  PHASE 2: EXECUTE (Pipeline branches + CLM watch)   │
│  FAST:      T1 → T4 OODA                           │
│  STANDARD:  T1 → T2 decompose → T4 OODA            │
│  FULL:      T1 → T2 → T3 graph/plan/guard → T4     │
│  EMERGENCY: T1 → T4 (1-3 cycles) + T5 protocol     │
│                                                     │
│  T6 cognitive_load_monitor after EVERY OODA cycle:  │
│   CONTINUE  → next cycle normally                   │
│   SIMPLIFY  → downgrade pipeline, continue          │
│   ESCALATE  → break loop, partial output            │
│   ABORT     → terminate loop immediately            │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│  PHASE 3: GATE-OUT (T6 Quality Chain)               │
│  T6: hallucination_monitor → GroundingReport        │
│  T6: confidence_calibrator → CalibratedConfidence   │
│  T6: noise_gate → FilteredOutput OR RejectedOutput  │
│   ├─ PASS → return annotated output                 │
│   ├─ RETRY (budget remaining) → back to Phase 2     │
│   └─ ESCALATE (budget exhausted) → partial + guide  │
└─────────────────────────────────────────────────────┘
```
 
---
 
## Files to Create
 
### 1. `redesign/conscious_observer/__init__.py`
Package init — exports `ConsciousObserver` and `run_conscious_observer`.
 
### 2. `redesign/conscious_observer/types.py`
New data contracts for the orchestrator boundary only. All domain types (ActivationMap, LoopResult, etc.) are imported from production `kernel/`.
 
Key types:
```python
class ProcessingMode(StrEnum):
    FAST = "fast"           # TRIVIAL/SIMPLE → T1 + T4
    STANDARD = "standard"   # MODERATE → T1 + T2 + T4
    FULL = "full"           # COMPLEX → T1 + T2 + T3 + T4
    EMERGENCY = "emergency" # CRITICAL → T1 + T4 + T5 (no planning)
 
class ObserverPhase(StrEnum):
    GATE_IN = "gate_in"
    EXECUTE = "execute"
    GATE_OUT = "gate_out"
 
class FeedbackAction(StrEnum):
    PASS = "pass"           # FilteredOutput → return to caller
    RETRY = "retry"         # RejectedOutput + budget remaining → re-execute T4
    SIMPLIFY = "simplify"   # CLM said SIMPLIFY
    ESCALATE = "escalate"   # Budget exhausted or CLM said ESCALATE
    ABORT = "abort"         # CLM said ABORT
 
class GateInResult(BaseModel):          # Internal Phase 1 result
    signal_tags: SignalTags
    modality_output: ModalityOutput
    classification: ClassificationResult
    cognitive_labels: CognitiveLabels
    entities: list[ValidatedEntity]
    activation_map: ActivationMap
    capability: CapabilityAssessment
    mode: ProcessingMode
    trace_id: str
    gate_in_duration_ms: float
 
class ObserverExecutionResult(BaseModel):  # Internal Phase 2 result
    loop_result: LoopResult
    raw_output: ToolOutput
    recent_decisions: list[Decision]
    recent_outputs: list[str]
    original_objective: str
    tokens_consumed: int
    cycles_completed: int
    execution_duration_ms: float
 
class ConsciousObserverResult(BaseModel):  # Final output
    trace_id: str
    agent_id: str
    mode: ProcessingMode
    phase_completed: ObserverPhase
    feedback_action: FeedbackAction
    filtered_output: FilteredOutput | None      # Success path
    partial_output: str | None                  # Escalation path
    escalation_guidance: RetryGuidance | None
    grounding_report: GroundingReport | None    # Always present (audit trail)
    calibrated_confidence: CalibratedConfidence | None
    total_duration_ms: float
    total_tokens: int
    total_cycles: int
    gate_in_ms: float
    execute_ms: float
    gate_out_ms: float
```
 
### 3. `redesign/conscious_observer/engine.py`
Main implementation — `ConsciousObserver` class + `run_conscious_observer()` module-level entry point.
 
**Key architectural decisions:**
 
- **Class-based + function wrapper**: `ConsciousObserver` holds injected `kit` and `identity` (immutable). `run_conscious_observer()` wraps it to match the `Signal → Result` protocol used by all kernel modules.
- **Phase 2 uses `run_ooda_cycle()` in a loop** (NOT `run_ooda_loop()`): `run_ooda_loop()` runs autonomously with no intercept points. Per-cycle CLM monitoring requires calling `run_ooda_cycle()` directly and checking CLM between every cycle. This is the core innovation.
- **SIMPLIFY is idempotent**: `_downgrade_activation_map()` reuses `_build_pipeline_templates()` from `activation_router/engine.py`. Already-at-TRIVIAL returns unchanged (no infinite loop).
- **Retry does NOT re-run Gate-In**: T1 perception is deterministic for a given input. On RETRY, only Phases 2 and 3 re-run.
- **Audit trail always emitted**: `ConsciousObserverResult` always carries `grounding_report` and `calibrated_confidence` even on success, for Vault persistence and T5 epoch commit.
 
**Class skeleton:**
```python
class ConsciousObserver:
    def __init__(self, kit: InferenceKit | None, identity: IdentityContext | None) -> None: ...
 
    async def process(
        self, raw_input: RawInput, objective: str,
        spawn_request: SpawnRequest | None = None,
        evidence: list[Origin] | None = None,
        rag_context: dict[str, Any] | None = None,
        trace_id: str = "",
    ) -> Result: ...
 
    async def _phase_gate_in(self, raw_input, objective, trace_id) -> GateInResult: ...
    async def _phase_execute(self, gate_result, objective, spawn_request, rag_context, trace_id) -> ObserverExecutionResult: ...
    async def _phase_gate_out(self, gate_result, exec_result, evidence, trace_id) -> ConsciousObserverResult: ...
 
    # Pipeline branches (called by _phase_execute)
    async def _execute_fast_path(...) -> ObserverExecutionResult: ...
    async def _execute_standard_path(...) -> ObserverExecutionResult: ...
    async def _execute_full_path(...) -> ObserverExecutionResult: ...
    async def _execute_emergency_path(...) -> ObserverExecutionResult: ...
 
    # Core CLM monitoring loop (shared by all branches)
    async def _run_ooda_with_clm(
        self, agent_state, event_stream, active_dag, objective,
        activation_map, rag_context, trace_id,
        max_cycles_override: int | None = None,
    ) -> tuple[LoopResult, list[Decision], list[str], int, int]: ...
 
 
async def run_conscious_observer(
    raw_input: RawInput, objective: str,
    kit: InferenceKit | None = None,
    identity: IdentityContext | None = None,
    ...,
) -> Result: ...
```
 
**Private helpers (all in engine.py):**
- `_extract_*()` functions — unpack `Result` → typed models (following existing extraction pattern)
- `_build_signal_tags()` — aggregates T1 outputs into `SignalTags` (T6 lingua franca)
- `_complexity_to_mode()` — maps `ComplexityLevel` → `ProcessingMode`
- `_downgrade_activation_map()` — CLM SIMPLIFY implementation
- `_compute_system_pressure()` — reads hardware metrics via `shared.hardware.get_pressure()`
- `_build_capability_escalation()` — short-circuit result when `can_handle=False`
- `_synthesize_loop_result()` — builds `LoopResult` from per-cycle accumulation
 
### 4. `redesign/conscious_observer/design.md`
Mandatory Mermaid documentation (per CLAUDE.md policy). Four diagrams:
 
1. **High-level three-phase flow** — Gate-In → Pipeline branch → CLM monitoring → Gate-Out with feedback loops
2. **Gate-In sequence diagram** — T1M → T1C → T1I → T1E → T6AR → T6SM step-by-step
3. **CLM monitoring flowchart** — Per-cycle CONTINUE/SIMPLIFY/ESCALATE/ABORT decision ladder
4. **Gate-Out quality sequence** — T6HM → T6CC → T6NG → PASS/RETRY/ESCALATE branches
 
---
 
## Files to Modify
 
### `shared/config.py` — Add to `KernelSettings` class (line ~630)
```python
# --- T6: Conscious Observer Orchestrator ---
conscious_observer_expected_cycle_ms: float = 2000.0
conscious_observer_emergency_max_cycles: int = 3
conscious_observer_gate_out_max_retries: int = 2
conscious_observer_entity_recognition_enabled: bool = True
conscious_observer_pressure_cache_ttl_seconds: int = 10
conscious_observer_abort_grounding_floor: float = 0.2
```
 
---
 
## Critical Existing Files to Reuse
 
| File | What to Reuse |
|------|---------------|
| `kernel/activation_router/engine.py` | `compute_activation_map()`, `_build_pipeline_templates()` (for downgrade), pressure-based logic |
| `kernel/ooda_loop/engine.py` | `run_ooda_cycle()` (NOT `run_ooda_loop()`) — the per-cycle intercept hook |
| `kernel/self_model/engine.py` | `assess_capability()`, `update_cognitive_state()` at each phase boundary |
| `kernel/cognitive_load_monitor/engine.py` | `monitor_cognitive_load()` — called after EVERY OODA cycle |
| `kernel/hallucination_monitor/engine.py` | `verify_grounding()` — Gate-Out step 1 |
| `kernel/confidence_calibrator/engine.py` | `run_confidence_calibration()` — Gate-Out step 2 |
| `kernel/noise_gate/engine.py` | `filter_output()`, `check_retry_budget()` — Gate-Out step 3 + feedback decision |
| `kernel/modality/engine.py` | `ingest()` — Gate-In first step |
| `kernel/classification/engine.py` | `classify()` — Gate-In step 2 |
| `kernel/intent_sentiment_urgency/engine.py` | `run_primitive_scorers()` — Gate-In step 3 |
| `kernel/entity_recognition/engine.py` | `extract_entities()` — Gate-In step 4 |
| `kernel/task_decomposition/engine.py` | `decompose_goal()` — STANDARD and FULL paths |
| `kernel/what_if_scenario/engine.py` | `simulate_outcomes()` — FULL path |
| `kernel/graph_synthesizer/engine.py` | `synthesize_plan()` — FULL path |
| `kernel/advanced_planning/engine.py` | `plan_advanced()` — FULL path |
| `kernel/reflection_and_guardrails/engine.py` | `run_pre_execution_check()` — FULL path conscience gate |
| `kernel/lifecycle_controller/engine.py` | `initialize_agent()` — Agent genesis before OODA |
| `kernel/short_term_memory/__init__.py` | `ShortTermMemory` — instantiated per `process()` call |
| `kernel/self_model/types.py` | `SignalTags` (lingua franca), `ProcessingPhase` (state tracking) |
| `shared/config.py` | `get_settings().kernel` — all threshold/limit references |
| `shared/logging/main.py` | `get_logger(__name__)` — all structured logging |
| `shared/standard_io.py` | `Result`, `ok()`, `fail()`, `create_data_signal()`, `Metrics`, `ModuleRef` |
 
---
 
## Implementation Sequence
 
1. **`redesign/conscious_observer/types.py`** — Types first; nothing else compiles without them
2. **`shared/config.py`** — Add 6 new `conscious_observer_*` settings before engine imports `get_settings()`
3. **`redesign/conscious_observer/engine.py`** — In sub-order:
   - All `_extract_*` helpers
   - `_build_signal_tags()`, `_complexity_to_mode()`, `_downgrade_activation_map()`, `_compute_system_pressure()`
   - `_phase_gate_in()` (pure T1 chain)
   - `_run_ooda_with_clm()` (core CLM intercept loop)
   - `_execute_fast_path()` and `_execute_standard_path()`
   - `_execute_full_path()` and `_execute_emergency_path()`
   - `_phase_execute()` dispatcher
   - `_phase_gate_out()` (quality gate + feedback)
   - `ConsciousObserver.process()` (assembler)
   - `run_conscious_observer()` (module-level entry point)
4. **`redesign/conscious_observer/__init__.py`** — Wire exports
5. **`redesign/conscious_observer/design.md`** — All four Mermaid diagrams
 
---
 
## Human Cognitive Analogy (The "Why")
 
| Human Behavior | System Equivalent |
|----------------|-------------------|
| "Can I handle this?" | `self_model.assess_capability()` → Gate-In capability check |
| "How hard is this?" | `activation_router.compute_activation_map()` → ProcessingMode selection |
| "Let me think about it" | T2/T3 planning phases (decompose → graph → plan) |
| "Now let me do it" | T4 OODA loop execution |
| "Am I going in circles?" | `cognitive_load_monitor` per-cycle SIMPLIFY/ESCALATE/ABORT |
| "Does this make sense?" | `hallucination_monitor.verify_grounding()` |
| "How sure am I?" | `confidence_calibrator.run_confidence_calibration()` |
| "Is this good enough to say?" | `noise_gate.filter_output()` → PASS or retry/escalate |
 
---
 
## Verification
 
Since tests are forbidden, verify the design by:
1. **Import check**: `python -c "from redesign.conscious_observer import ConsciousObserver"` — must resolve without errors
2. **Type coherence**: Run `mypy redesign/conscious_observer/` — all type annotations must pass
3. **Mermaid rendering**: Open `design.md` in a Mermaid renderer (e.g., GitHub preview) — all four diagrams must render correctly
4. **Config presence**: `python -c "from shared.config import get_settings; s = get_settings().kernel; print(s.conscious_observer_expected_cycle_ms)"` — must print `2000.0`
5. **Circular import check**: `python -c "import redesign.conscious_observer; import kernel"` — no circular import errors
