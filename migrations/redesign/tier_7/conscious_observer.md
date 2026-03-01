# Plan: Tier 7 `ConsciousObserver` — Human Kernel Apex
 
## Context
 
The Human Kernel has 6 fully-implemented Tier 6 modules (self_model, activation_router, cognitive_load_monitor, hallucination_monitor, confidence_calibrator, noise_gate) but no top-level orchestrator that ties them together. This means there is no single entry point that processes any input end-to-end like a human does.
 
**Tier 7** is the apex of the Human Kernel — the only module at this tier. It wraps all Tier 1–6 modules into one coherent cognitive pipeline, mimicking how a human receives input and responds:
 
> _Perceive → Assess self → Route attention → Think → Monitor load → Verify → Speak_
 
**Location**: `kernel/conscious_observer/` — directly in the production kernel (not redesign/).
 
---
 
## Architecture: Three Phases + Four Pipeline Modes
 
```
RawInput (any modality)
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  PHASE 1: GATE-IN (T1 Perception + T5 Genesis + T6) │
│  T5: initialize_agent → load_profile → identity ctx │
│  T1: ingest → classify → ISU scorers → entities     │
│  T6: self_model → capability check                  │
│   ├─ not capable → Escalate immediately              │
│  T6: activation_router → ActivationMap + Mode       │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│  PHASE 2: EXECUTE (Pipeline branches + CLM watch)   │
│  FAST (TRIVIAL/SIMPLE):  T4 OODA                    │
│  STANDARD (MODERATE):    T2 decompose → T4 OODA     │
│  FULL (COMPLEX):         T2→T3 graph/plan→T4 OODA   │
│  EMERGENCY (CRITICAL):   T4 (capped cycles)+T5      │
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
│   ├─ PASS   → return annotated FilteredOutput       │
│   ├─ RETRY  (budget remaining) → back to Phase 2    │
│   └─ ESCALATE (budget exhausted) → partial + guide  │
└─────────────────────────────────────────────────────┘
```
 
---
 
## Files to Create
 
### 1. `kernel/conscious_observer/__init__.py`
Package init — exports `ConsciousObserver` and `run_conscious_observer`.
 
### 2. `kernel/conscious_observer/types.py`
New data contracts for the orchestrator boundary. Domain types (ActivationMap, LoopResult, etc.) are imported from existing kernel submodules.
 
Key types:
```python
class ProcessingMode(StrEnum):
    FAST = "fast"           # TRIVIAL/SIMPLE → T4 direct
    STANDARD = "standard"   # MODERATE → T2 + T4
    FULL = "full"           # COMPLEX → T2 + T3 + T4
    EMERGENCY = "emergency" # CRITICAL → T4 (capped) + T5 protocol
 
class ObserverPhase(StrEnum):
    GATE_IN = "gate_in"
    EXECUTE = "execute"
    GATE_OUT = "gate_out"
    ESCALATED = "escalated"  # Capability gap or CLM escalation
    ABORTED = "aborted"      # CLM abort signal
 
class GateInResult(BaseModel):
    identity_context: IdentityContext
    signal_tags: SignalTags
    modality_output: ModalityOutput
    classification: ClassificationResult
    cognitive_labels: CognitiveLabels
    entities: list[ValidatedEntity]
    activation_map: ActivationMap
    capability: CapabilityAssessment
    mode: ProcessingMode
    gate_in_duration_ms: float
 
class ObserverExecuteResult(BaseModel):
    loop_result: LoopResult
    raw_artifact: str           # Synthesized content from loop artifacts
    recent_decisions: list[Decision]
    recent_outputs: list[str]
    objective: str
    total_cycles: int
    was_simplified: bool
    was_escalated: bool
    was_aborted: bool
    execute_duration_ms: float
 
class ConsciousObserverResult(BaseModel):
    trace_id: str
    agent_id: str
    mode: ProcessingMode
    final_phase: ObserverPhase
    filtered_output: FilteredOutput | None      # Success path
    partial_output: str | None                  # Escalation path
    escalation_guidance: RetryGuidance | None
    grounding_report: GroundingReport | None    # Always present (audit trail)
    calibrated_confidence: CalibratedConfidence | None
    total_duration_ms: float
    total_cycles: int
    gate_in_ms: float
    execute_ms: float
    gate_out_ms: float
    was_simplified: bool
    was_escalated: bool
    was_aborted: bool
```
 
### 3. `kernel/conscious_observer/engine.py`
Main implementation — `ConsciousObserver` class + `run_conscious_observer()` module-level entry point.
 
**Key architectural decisions:**
 
- **Class-based + function wrapper**: `ConsciousObserver` holds an injected `kit`. `run_conscious_observer()` wraps it to match the `Signal → Result` protocol used by all kernel modules.
- **Phase 2 uses `run_ooda_cycle()` in a controlled loop** (NOT `run_ooda_loop()`): The inner `run_ooda_loop()` has no intercept points. Per-cycle CLM monitoring requires calling `run_ooda_cycle()` directly and checking CLM between every cycle. This is the core innovation of Tier 7.
- **SIMPLIFY is idempotent**: `_downgrade_activation_map()` reuses `select_pipeline()` + `_build_pipeline_templates()` from `activation_router/engine.py`. Already at TRIVIAL → returns unchanged.
- **Retry skips Gate-In**: T1 perception is deterministic for a given input. On Gate-Out RETRY, only Phases 2 and 3 re-run.
- **Audit trail always emitted**: `ConsciousObserverResult` always carries `grounding_report` and `calibrated_confidence` for Vault persistence.
- **Agent genesis inside Gate-In**: `initialize_agent()` + `load_cognitive_profile()` + `set_identity_constraints()` are called during Gate-In to produce the `IdentityContext` passed to all lower tiers.
 
**Class skeleton:**
```python
class ConsciousObserver:
    def __init__(self, kit: InferenceKit | None = None) -> None: ...
 
    async def process(
        self,
        raw_input: RawInput,
        spawn_request: SpawnRequest,
        evidence: list[Origin] | None = None,
        rag_context: dict[str, Any] | None = None,
        trace_id: str = "",
    ) -> Result: ...                     # Contains ConsciousObserverResult
 
    # Internal phases
    async def _phase_gate_in(
        self, raw_input: RawInput, spawn_request: SpawnRequest, trace_id: str
    ) -> GateInResult: ...
 
    async def _phase_execute(
        self, gate: GateInResult, spawn_request: SpawnRequest,
        rag_context: dict[str, Any] | None, trace_id: str
    ) -> ObserverExecuteResult: ...
 
    async def _phase_gate_out(
        self, gate: GateInResult, exec_res: ObserverExecuteResult,
        evidence: list[Origin], trace_id: str,
        gate_in_ms: float, execute_ms: float, start_total: float,
    ) -> ConsciousObserverResult: ...
 
    # Pipeline branches (called by _phase_execute)
    async def _execute_fast_path(
        self, gate: GateInResult, spawn_request: SpawnRequest,
        rag_context: dict[str, Any] | None
    ) -> ObserverExecuteResult: ...
 
    async def _execute_standard_path(
        self, gate: GateInResult, spawn_request: SpawnRequest,
        rag_context: dict[str, Any] | None
    ) -> ObserverExecuteResult: ...
 
    async def _execute_full_path(
        self, gate: GateInResult, spawn_request: SpawnRequest,
        rag_context: dict[str, Any] | None
    ) -> ObserverExecuteResult: ...
 
    async def _execute_emergency_path(
        self, gate: GateInResult, spawn_request: SpawnRequest,
        rag_context: dict[str, Any] | None
    ) -> ObserverExecuteResult: ...
 
    # Core CLM monitoring loop (shared by all pipeline branches)
    async def _run_ooda_with_clm(
        self,
        agent_state: AgentState,
        stm: ShortTermMemory,
        active_dag: ExecutableDAG | None,
        objective: str,
        activation_map: ActivationMap,
        rag_context: dict[str, Any] | None,
        trace_id: str,
        max_cycles_override: int | None = None,
    ) -> tuple[LoopResult, list[Decision], list[str], bool, bool, bool]:
        # Returns: (loop_result, decisions, outputs, was_simplified, was_escalated, was_aborted)
        ...
 
 
# Module-level entry point (matches Signal → Result protocol)
async def run_conscious_observer(
    raw_input: RawInput,
    spawn_request: SpawnRequest,
    kit: InferenceKit | None = None,
    evidence: list[Origin] | None = None,
    rag_context: dict[str, Any] | None = None,
    trace_id: str = "",
) -> Result: ...
```
 
**Private helpers (module-level in engine.py):**
- `_extract_modality_output(result)` — unpack `Result` → `ModalityOutput`
- `_extract_classification(result)` — unpack `Result` → `ClassificationResult`
- `_extract_cognitive_labels(result)` — unpack `Result` → `CognitiveLabels`
- `_extract_entities(result)` — unpack `Result` → `list[ValidatedEntity]`
- `_extract_activation_map(result)` — unpack `Result` → `ActivationMap`
- `_extract_load_recommendation(result)` — unpack `Result` → `LoadRecommendation`
- `_extract_grounding_report(result)` — unpack `Result` → `GroundingReport`
- `_extract_calibrated_confidence(result)` — unpack `Result` → `CalibratedConfidence`
- `_extract_filter_result(result)` — unpack `Result` → `FilteredOutput | RejectedOutput`
- `_extract_subtasks(result)` — unpack `Result` → `list[SubTaskItem]`
- `_extract_dag(result)` — unpack `Result` → `ExecutableDAG`
- `_build_signal_tags(classification, labels, entities, modality_output)` → `SignalTags`
- `_complexity_to_mode(complexity_level)` → `ProcessingMode`
- `_downgrade_activation_map(activation_map)` → `ActivationMap` (one level lower)
- `_build_agent_state(identity_context, spawn_request)` → `AgentState`
- `_build_world_state(spawn_request, identity_context, rag_context)` → `WorldState`
- `_build_tool_output(loop_result, trace_id)` → `ToolOutput` (for Gate-Out)
- `_synthesize_artifact(loop_result)` → `str` (human-readable summary of loop output)
 
---
 
## Files to Modify
 
### `shared/config.py` — Add to `KernelSettings` (after line 822, after noise gate settings)
```python
# --- T7: Conscious Observer ---
conscious_observer_emergency_max_cycles: int = 3
conscious_observer_expected_cycle_ms: float = 2000.0
conscious_observer_simplify_max_steps: int = 2
```
 
### `kernel/__init__.py` — Add Tier 7 section
After the existing Tier 6 export block (after `noise_gate` exports), add:
```python
# ============================================================================
# Tier 7: Human Kernel Apex (Conscious Observer Orchestrator)
# ============================================================================
from kernel.conscious_observer import (
    ConsciousObserver,
    ConsciousObserverResult,
    GateInResult,
    ObserverExecuteResult,
    ObserverPhase,
    ProcessingMode,
    run_conscious_observer,
)
```
And add all names to `__all__`.
 
Also update the module docstring in `kernel/__init__.py` to add:
```
Tier 7: Human Kernel Apex (kernel/) → Conscious Observer
```
 
---
 
## Critical Existing Files to Reuse
 
| File | What to Reuse |
|------|---------------|
| `kernel/lifecycle_controller/engine.py` | `initialize_agent()`, `load_cognitive_profile()`, `set_identity_constraints()` — Gate-In genesis |
| `kernel/modality/engine.py` | `ingest()` — Gate-In step 1 |
| `kernel/classification/engine.py` | `classify()` — Gate-In step 2 |
| `kernel/intent_sentiment_urgency/engine.py` | `run_primitive_scorers()` — Gate-In step 3 |
| `kernel/entity_recognition/engine.py` | `extract_entities()` — Gate-In step 4 |
| `kernel/self_model/engine.py` | `assess_capability()`, `update_cognitive_state()`, `get_calibration_history()` |
| `kernel/activation_router/engine.py` | `compute_activation_map()`, `select_pipeline()`, `_build_pipeline_templates()` |
| `kernel/task_decomposition/engine.py` | `decompose_goal()` — STANDARD + FULL paths |
| `kernel/what_if_scenario/engine.py` | `simulate_outcomes()` — FULL path |
| `kernel/graph_synthesizer/engine.py` | `synthesize_plan()` — FULL path |
| `kernel/advanced_planning/engine.py` | `plan_advanced()` — FULL path |
| `kernel/reflection_and_guardrails/engine.py` | `run_pre_execution_check()` — FULL path conscience gate |
| `kernel/short_term_memory/__init__.py` | `ShortTermMemory` — instantiated fresh per `process()` call |
| `kernel/ooda_loop/engine.py` | `run_ooda_cycle()` (NOT `run_ooda_loop()`) — the per-cycle intercept hook |
| `kernel/cognitive_load_monitor/engine.py` | `monitor_cognitive_load()` — called after EVERY OODA cycle |
| `kernel/hallucination_monitor/engine.py` | `verify_grounding()` — Gate-Out step 1 |
| `kernel/confidence_calibrator/engine.py` | `run_confidence_calibration()` — Gate-Out step 2 |
| `kernel/noise_gate/engine.py` | `filter_output()`, `check_retry_budget()`, `clear_retry_budget()` — Gate-Out step 3 |
| `shared/config.py` | `get_settings().kernel` — all thresholds and limits |
| `shared/logging/main.py` | `get_logger(__name__)` |
| `shared/standard_io.py` | `Result`, `ok()`, `fail()`, `create_data_signal()`, `Metrics`, `ModuleRef` |
| `shared/id_and_hash.py` | `generate_id()` — for trace_id and output_id generation |
 
---
 
## Implementation Sequence
 
1. **`kernel/conscious_observer/types.py`** — Define `ProcessingMode`, `ObserverPhase`, `GateInResult`, `ObserverExecuteResult`, `ConsciousObserverResult`
2. **`shared/config.py`** — Add 3 `conscious_observer_*` settings to `KernelSettings`
3. **`kernel/conscious_observer/engine.py`** — In sub-order:
   - All `_extract_*` helpers (unpack Result → typed models)
   - `_build_signal_tags()`, `_complexity_to_mode()`, `_downgrade_activation_map()`, `_build_agent_state()`, `_build_world_state()`, `_build_tool_output()`, `_synthesize_artifact()`
   - `_phase_gate_in()` — T5 genesis + T1 chain + T6 capability/routing
   - `_run_ooda_with_clm()` — core CLM intercept loop using `run_ooda_cycle()`
   - `_execute_fast_path()`, `_execute_standard_path()`, `_execute_full_path()`, `_execute_emergency_path()`
   - `_phase_execute()` — mode dispatcher
   - `_phase_gate_out()` — T6HM → T6CC → T6NG with retry logic
   - `ConsciousObserver.process()` — assembler
   - `run_conscious_observer()` — module-level entry point
4. **`kernel/conscious_observer/__init__.py`** — Wire all exports
5. **`kernel/__init__.py`** — Add Tier 7 import block + `__all__` entries + docstring update
 
---
 
## Human Cognitive Analogy
 
| Human Behavior | Tier 7 Implementation |
|----------------|----------------------|
| "Who am I? What role am I playing?" | `initialize_agent()` + `load_cognitive_profile()` + `set_identity_constraints()` |
| "What is this input?" | T1: `ingest()` → `classify()` → `run_primitive_scorers()` → `extract_entities()` |
| "Can I handle this?" | `self_model.assess_capability()` |
| "How hard is this? What approach?" | `activation_router.compute_activation_map()` → `ProcessingMode` |
| "Let me plan first" | T2: `decompose_goal()` → T3: `synthesize_plan()` + `plan_advanced()` (FULL only) |
| "Now let me act" | T4: `run_ooda_cycle()` in controlled loop |
| "Am I going in circles? Overwhelmed?" | T6: `monitor_cognitive_load()` per cycle → CONTINUE/SIMPLIFY/ESCALATE/ABORT |
| "Does my answer make sense?" | T6: `hallucination_monitor.verify_grounding()` |
| "How sure am I really?" | T6: `confidence_calibrator.run_confidence_calibration()` |
| "Is this good enough to say?" | T6: `noise_gate.filter_output()` → PASS or retry/escalate |
 
---
 
## Verification
 
Since tests are forbidden, verify by:
1. **Import check**: `python -c "from kernel.conscious_observer import ConsciousObserver"` — must resolve without errors
2. **Config presence**: `python -c "from shared.config import get_settings; s = get_settings().kernel; print(s.conscious_observer_expected_cycle_ms)"` — must print `2000.0`
3. **Kernel exports**: `python -c "from kernel import ConsciousObserver, run_conscious_observer"` — must resolve without errors
4. **Circular import check**: `python -c "import kernel.conscious_observer; import kernel"` — no circular import errors
