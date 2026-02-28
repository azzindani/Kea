"""
Tier 7 Conscious Observer — Engine.

The Human Kernel Apex: the sole top-level entry point for all inputs.

Orchestrates the full cognitive pyramid across three phases:
    Phase 1 — GATE-IN:  T5 agent genesis, T1 perception, T6 routing
    Phase 2 — EXECUTE:  T2/T3/T4 pipeline (mode-selected), T6 CLM per cycle
    Phase 3 — GATE-OUT: T6 grounding → confidence → noise gate → retry

This mimics how a human processes input:
    "Can I handle this?" → "How hard? Which approach?" → "Do the work"
    → "Am I going in circles?" → "Does my answer hold up?" → "Say it"

CRITICAL: Phase 2 uses run_ooda_cycle() in a CONTROLLED LOOP (not
run_ooda_loop()) so the Cognitive Load Monitor can intercept between
every cycle and apply CONTINUE/SIMPLIFY/ESCALATE/ABORT decisions.
"""

from __future__ import annotations

import time
from typing import Any

from kernel.activation_router.engine import (
    compute_activation_map,
    select_pipeline,
)
from kernel.activation_router.types import ActivationMap, ComplexityLevel
from kernel.advanced_planning.engine import plan_advanced
from kernel.advanced_planning.types import PlanningConstraints
from kernel.classification.engine import classify
from kernel.classification.types import (
    ClassificationResult,
    ClassProfileRules,
    FallbackTrigger,
)
from kernel.cognitive_load_monitor.engine import monitor_cognitive_load
from kernel.cognitive_load_monitor.types import CycleTelemetry, LoadAction, LoadRecommendation
from kernel.confidence_calibrator.engine import run_confidence_calibration
from kernel.confidence_calibrator.types import CalibratedConfidence
from kernel.entity_recognition.engine import extract_entities
from kernel.entity_recognition.types import ValidatedEntity
from kernel.graph_synthesizer.engine import synthesize_plan
from kernel.graph_synthesizer.types import ExecutableDAG
from kernel.hallucination_monitor.engine import verify_grounding
from kernel.hallucination_monitor.types import GroundingReport, Origin
from kernel.intent_sentiment_urgency.engine import run_primitive_scorers
from kernel.intent_sentiment_urgency.types import CognitiveLabels
from kernel.lifecycle_controller.engine import (
    initialize_agent,
    load_cognitive_profile,
    set_identity_constraints,
)
from kernel.lifecycle_controller.types import IdentityContext, SpawnRequest
from kernel.modality.engine import ingest
from kernel.modality.types import ModalityOutput, RawInput
from kernel.noise_gate.engine import clear_retry_budget, filter_output
from kernel.noise_gate.types import FilteredOutput, RejectedOutput, ToolOutput
from kernel.ooda_loop.engine import run_ooda_cycle
from kernel.ooda_loop.types import (
    AgentState,
    AgentStatus,
    CycleAction,
    Decision,
    DecisionAction,
    LoopResult,
    LoopTerminationReason,
    MacroObjective,
)
from kernel.reflection_and_guardrails.engine import run_pre_execution_check
from kernel.self_model.engine import (
    assess_capability,
    get_calibration_history,
    update_cognitive_state,
)
from kernel.self_model.types import ProcessingPhase, SignalTags
from kernel.short_term_memory.engine import ShortTermMemory
from kernel.task_decomposition.engine import decompose_goal
from kernel.task_decomposition.types import SubTaskItem, WorldState
from kernel.what_if_scenario.engine import simulate_outcomes
from shared.config import get_settings
from shared.id_and_hash import generate_id
from shared.inference_kit import InferenceKit
from shared.logging.main import get_logger
from shared.standard_io import (
    Metrics,
    ModuleRef,
    Result,
    create_data_signal,
    fail,
    ok,
    processing_error,
)

from .types import (
    ConsciousObserverResult,
    GateInResult,
    ObserverExecuteResult,
    ObserverPhase,
    ProcessingMode,
)

log = get_logger(__name__)

_MODULE = "conscious_observer"
_TIER = 7


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Extraction Helpers — unpack Result → typed models
# ============================================================================


def _extract_modality_output(result: Result) -> ModalityOutput:
    if result.error or not result.signals:
        raise RuntimeError(f"ingest failed: {result.error}")
    return ModalityOutput(**result.signals[0].body["data"])


def _extract_classification(result: Result) -> ClassificationResult | FallbackTrigger:
    if result.error or not result.signals:
        raise RuntimeError(f"classify failed: {result.error}")
    
    signal = result.signals[0]
    data = signal.body["data"]
    
    if signal.schema == "FallbackTrigger" or "reason" in data:
        return FallbackTrigger(**data)
    return ClassificationResult(**data)


def _extract_cognitive_labels(result: Result) -> CognitiveLabels:
    if result.error or not result.signals:
        raise RuntimeError(f"run_primitive_scorers failed: {result.error}")
    return CognitiveLabels(**result.signals[0].body["data"])


def _extract_entities(result: Result) -> list[ValidatedEntity]:
    if result.error or not result.signals:
        return []
    raw = result.signals[0].body["data"]
    items = raw if isinstance(raw, list) else raw.get("entities", [])
    return [ValidatedEntity(**e) if isinstance(e, dict) else e for e in items]


def _extract_activation_map(result: Result) -> ActivationMap:
    if result.error or not result.signals:
        raise RuntimeError(f"compute_activation_map failed: {result.error}")
    return ActivationMap(**result.signals[0].body["data"])


def _extract_load_recommendation(result: Result) -> LoadRecommendation:
    if result.error or not result.signals:
        raise RuntimeError(f"monitor_cognitive_load failed: {result.error}")
    return LoadRecommendation(**result.signals[0].body["data"])


def _extract_grounding_report(result: Result) -> GroundingReport:
    if result.error or not result.signals:
        raise RuntimeError(f"verify_grounding failed: {result.error}")
    return GroundingReport(**result.signals[0].body["data"])


def _extract_calibrated_confidence(result: Result) -> CalibratedConfidence:
    if result.error or not result.signals:
        raise RuntimeError(f"run_confidence_calibration failed: {result.error}")
    return CalibratedConfidence(**result.signals[0].body["data"])


def _extract_filter_result(result: Result) -> FilteredOutput | RejectedOutput:
    if result.error or not result.signals:
        raise RuntimeError(f"filter_output failed: {result.error}")
    data = result.signals[0].body["data"]
    if data.get("passed", True):
        return FilteredOutput(**data)
    return RejectedOutput(**data)


def _extract_subtasks(result: Result) -> list[SubTaskItem]:
    if result.error or not result.signals:
        return []
    raw = result.signals[0].body["data"]
    items = raw if isinstance(raw, list) else raw.get("subtasks", [])
    return [SubTaskItem(**s) if isinstance(s, dict) else s for s in items]


def _extract_dag(result: Result) -> ExecutableDAG | None:
    if result.error or not result.signals:
        return None
    data = result.signals[0].body["data"]
    if isinstance(data, dict) and "dag" in data:
        # From synthesize_plan nesting
        return ExecutableDAG(**data["dag"])
    return ExecutableDAG(**data)


# ============================================================================
# Build Helpers — compose inputs for lower tiers
# ============================================================================


def _build_signal_tags(
    classification: ClassificationResult | FallbackTrigger,
    labels: CognitiveLabels,
    entities: list[ValidatedEntity],
    modality_output: ModalityOutput,
) -> SignalTags:
    """Aggregate Tier 1 outputs into the SignalTags lingua franca for Tier 6."""
    urgency_str = labels.urgency.band.value.lower()   # e.g., "normal", "high", "critical"
    intent_str = labels.intent.primary.value           # e.g., "QUERY", "CREATE"
    domain = classification.top_label or "general"

    # Derive structural complexity hint from classification confidence
    conf = classification.confidence
    if conf >= 0.8:
        complexity_hint = "simple"
    elif conf >= 0.5:
        complexity_hint = "moderate"
    else:
        complexity_hint = "complex"
    
    if isinstance(classification, FallbackTrigger):
        complexity_hint = "complex"  # Fallback entries are inherently complex to resolve

    return SignalTags(
        urgency=urgency_str,
        domain=domain,
        complexity=complexity_hint,
        source_type=modality_output.modality.value,
        intent=intent_str,
        entity_count=len(entities),
        required_skills=[],
        required_tools=[],
    )


def _complexity_to_mode(complexity: ComplexityLevel) -> ProcessingMode:
    """Map activation router complexity to a T7 processing mode."""
    mapping = {
        ComplexityLevel.TRIVIAL: ProcessingMode.FAST,
        ComplexityLevel.SIMPLE: ProcessingMode.FAST,
        ComplexityLevel.MODERATE: ProcessingMode.STANDARD,
        ComplexityLevel.COMPLEX: ProcessingMode.FULL,
        ComplexityLevel.CRITICAL: ProcessingMode.EMERGENCY,
    }
    return mapping.get(complexity, ProcessingMode.STANDARD)


def _downgrade_activation_map(activation_map: ActivationMap) -> ActivationMap:
    """Downgrade the pipeline by one complexity level for CLM SIMPLIFY.

    Delegates to the activation_router's select_pipeline() so pressure
    thresholds and template definitions remain config-driven.
    Idempotent: already at TRIVIAL returns unchanged.
    """
    if activation_map.pipeline is None:
        return activation_map

    level_order = [
        ComplexityLevel.TRIVIAL,
        ComplexityLevel.SIMPLE,
        ComplexityLevel.MODERATE,
        ComplexityLevel.COMPLEX,
    ]
    current = activation_map.pipeline.complexity_level
    if current == ComplexityLevel.CRITICAL:
        return activation_map  # Emergency path never downgraded

    idx = level_order.index(current) if current in level_order else 0
    if idx == 0:
        return activation_map  # Already at minimum

    downgraded_level = level_order[idx - 1]
    new_pipeline = select_pipeline(downgraded_level, pressure=0.0)

    from kernel.activation_router.types import ModuleActivation

    new_states = {m: ModuleActivation.ACTIVE for m in new_pipeline.active_modules}
    return ActivationMap(
        pipeline=new_pipeline,
        module_states=new_states,
        pressure_downgraded=True,
        original_complexity=current,
        cache_hit=False,
    )


def _build_agent_state(
    identity_context: IdentityContext,
    spawn_request: SpawnRequest,
) -> AgentState:
    """Construct the initial AgentState for the OODA loop."""
    objective = MacroObjective(
        objective_id=generate_id("obj"),
        description=spawn_request.objective,
        priority=0,
        completed=False,
    )
    return AgentState(
        agent_id=identity_context.agent_id,
        status=AgentStatus.ACTIVE,
        current_objectives=[objective],
        active_dag_id=None,
        context=dict(spawn_request.context),
        cycle_count=0,
        total_cost=0.0,
    )


def _build_world_state(
    spawn_request: SpawnRequest,
    identity_context: IdentityContext,
    rag_context: dict[str, Any] | None,
) -> WorldState:
    """Construct WorldState for Tier 2 task decomposition."""
    ctx: dict[str, str] = {k: str(v) for k, v in spawn_request.context.items()}
    if rag_context:
        ctx.update({k: str(v) for k, v in rag_context.items()})
    return WorldState(
        goal=spawn_request.objective,
        context=ctx,
        available_skills=list(identity_context.skills),
        available_tools=list(identity_context.tools_allowed),
        knowledge_domains=list(identity_context.knowledge_domains),
    )


def _build_tool_output(loop_result: LoopResult, trace_id: str) -> ToolOutput:
    """Wrap the OODA loop result as a ToolOutput for Gate-Out quality chain."""
    content = _synthesize_artifact(loop_result)
    return ToolOutput(
        output_id=generate_id("out"),
        content=content,
        metadata={
            "trace_id": trace_id,
            "agent_id": loop_result.agent_id,
            "total_cycles": loop_result.total_cycles,
            "termination_reason": loop_result.termination_reason.value,
            "objectives_completed": loop_result.objectives_completed,
        },
        source_node_id=loop_result.artifacts_produced[-1] if loop_result.artifacts_produced else "",
        source_dag_id="",
    )


def _synthesize_artifact(loop_result: LoopResult) -> str:
    """Produce a human-readable summary of what the OODA loop accomplished."""
    parts: list[str] = []

    if loop_result.objectives_completed:
        parts.append(
            f"Completed objectives: {', '.join(loop_result.objectives_completed)}"
        )
    if loop_result.artifacts_produced:
        parts.append(
            f"Produced artifacts: {', '.join(loop_result.artifacts_produced[:10])}"
        )
    if loop_result.final_state:
        context = loop_result.final_state.get("context", {})
        if context:
            summaries = [f"{k}={v}" for k, v in list(context.items())[:5]]
            parts.append(f"Execution context: {'; '.join(summaries)}")

    if not parts:
        parts.append(
            f"Loop completed after {loop_result.total_cycles} cycles "
            f"({loop_result.termination_reason.value})"
        )

    return " | ".join(parts)


# ============================================================================
# ConsciousObserver — Tier 7 Orchestrator Class
# ============================================================================


class ConsciousObserver:
    """Tier 7 — Human Kernel Apex.

    The sole top-level entry point that routes any raw input through the
    full Tier 1–6 cognitive pyramid. Mimics human conscious processing:

        Gate-In  → Who am I? What is this? Can I handle it? How hard?
        Execute  → Think, act, and self-monitor in real time
        Gate-Out → Does my answer hold? Am I sure? Is it good enough?

    Usage::

        observer = ConsciousObserver(kit=inference_kit)
        result = await observer.process(raw_input, spawn_request)
    """

    def __init__(self, kit: InferenceKit | None = None) -> None:
        self._kit = kit

    # ------------------------------------------------------------------
    # Public Entry Point
    # ------------------------------------------------------------------

    async def process(
        self,
        raw_input: RawInput,
        spawn_request: SpawnRequest,
        evidence: list[Origin] | None = None,
        rag_context: dict[str, Any] | None = None,
        trace_id: str = "",
    ) -> Result:
        """Full three-phase cognitive processing pipeline.

        Args:
            raw_input:      Any modality (text/audio/image/video/doc).
            spawn_request:  Corporate Kernel directive — role, objective, budgets.
            evidence:       Optional external evidence for Gate-Out grounding.
            rag_context:    Optional RAG-enriched context for OODA orientation.
            trace_id:       Propagated trace ID (auto-generated if empty).

        Returns:
            Result containing ConsciousObserverResult.
        """
        ref = _ref("process")
        start_total = time.perf_counter()

        if not trace_id:
            trace_id = generate_id("t7")

        bound_log = log.bind(
            trace_id=trace_id,
            objective=spawn_request.objective,
            role=spawn_request.role,
        )
        bound_log.info("ConsciousObserver.process started")

        try:
            # ─── PHASE 1: GATE-IN ────────────────────────────────────────
            gate_in_start = time.perf_counter()
            gate_in = await self._phase_gate_in(raw_input, spawn_request, trace_id)
            gate_in_ms = (time.perf_counter() - gate_in_start) * 1000

            bound_log.info(
                "Gate-In complete",
                mode=gate_in.mode.value,
                capable=gate_in.capability.can_handle,
                gate_in_ms=round(gate_in_ms, 2),
            )

            # Early exit — capability gap
            if not gate_in.capability.can_handle:
                bound_log.warning(
                    "Capability gap — escalating before execution",
                    gap=gate_in.capability.gap.model_dump() if gate_in.capability.gap else None,
                )
                result_data = ConsciousObserverResult(
                    trace_id=trace_id,
                    agent_id=gate_in.identity_context.agent_id,
                    mode=gate_in.mode,
                    final_phase=ObserverPhase.ESCALATED,
                    partial_output="Agent cannot handle this input.",
                    total_duration_ms=(time.perf_counter() - start_total) * 1000,
                    gate_in_ms=gate_in_ms,
                )
                return ok(
                    signals=[
                        create_data_signal(
                            data=result_data.model_dump(),
                            schema="ConsciousObserverResult",
                            origin=ref,
                            trace_id=trace_id,
                            tags={"phase": ObserverPhase.ESCALATED.value},
                        )
                    ],
                    metrics=Metrics(
                        duration_ms=(time.perf_counter() - start_total) * 1000,
                        module_ref=ref,
                    ),
                )

            # ─── PHASE 2: EXECUTE ────────────────────────────────────────
            execute_start = time.perf_counter()
            exec_res = await self._phase_execute(
                gate_in, spawn_request, rag_context, trace_id
            )
            execute_ms = (time.perf_counter() - execute_start) * 1000

            bound_log.info(
                "Execute complete",
                cycles=exec_res.total_cycles,
                simplified=exec_res.was_simplified,
                escalated=exec_res.was_escalated,
                aborted=exec_res.was_aborted,
                execute_ms=round(execute_ms, 2),
            )

            # ─── PHASE 3: GATE-OUT ───────────────────────────────────────
            gate_out_start = time.perf_counter()
            observer_result = await self._phase_gate_out(
                gate_in,
                exec_res,
                evidence or [],
                trace_id,
                gate_in_ms=gate_in_ms,
                execute_ms=execute_ms,
                start_total=start_total,
            )
            gate_out_ms = (time.perf_counter() - gate_out_start) * 1000

            bound_log.info(
                "Gate-Out complete",
                phase=observer_result.final_phase.value,
                gate_out_ms=round(gate_out_ms, 2),
                total_ms=round(observer_result.total_duration_ms, 2),
            )

            elapsed_total = (time.perf_counter() - start_total) * 1000
            metrics = Metrics(duration_ms=elapsed_total, module_ref=ref)

            signal = create_data_signal(
                data=observer_result.model_dump(),
                schema="ConsciousObserverResult",
                origin=ref,
                trace_id=trace_id,
                tags={
                    "agent_id": observer_result.agent_id,
                    "mode": observer_result.mode.value,
                    "phase": observer_result.final_phase.value,
                    "cycles": str(observer_result.total_cycles),
                    "simplified": str(observer_result.was_simplified),
                    "escalated": str(observer_result.was_escalated),
                },
            )

            return ok(signals=[signal], metrics=metrics)

        except Exception as exc:
            elapsed = (time.perf_counter() - start_total) * 1000
            metrics = Metrics(duration_ms=elapsed, module_ref=ref)
            error = processing_error(
                message=f"ConsciousObserver.process failed: {exc}",
                source=ref,
                detail={
                    "trace_id": trace_id,
                    "objective": spawn_request.objective,
                    "error_type": type(exc).__name__,
                },
            )
            log.error(
                "ConsciousObserver.process failed",
                trace_id=trace_id,
                error=str(exc),
            )
            return fail(error=error, metrics=metrics)

    # ------------------------------------------------------------------
    # Phase 1: Gate-In
    # ------------------------------------------------------------------

    async def _phase_gate_in(
        self,
        raw_input: RawInput,
        spawn_request: SpawnRequest,
        trace_id: str,
    ) -> GateInResult:
        """T5 agent genesis + T1 perception + T6 capability/routing.

        Sub-steps (in order):
            1. Initialize agent identity (T5)
            2. Load cognitive profile (T5)
            3. Set immutable identity constraints (T5)
            4. Ingest raw input (T1 Modality)
            5. Classify signal (T1 Classification)
            6. Score intent/sentiment/urgency (T1 ISU)
            7. Extract entities (T1 NER)
            8. Assess self-capability (T6 Self-Model)
            9. Compute activation map + pipeline mode (T6 Activation Router)
        """
        start = time.perf_counter()

        # 1. T5: Agent genesis
        identity = await initialize_agent(spawn_request)

        # 2. T5: Load cognitive profile
        profile = await load_cognitive_profile(spawn_request.profile_id)

        # 3. T5: Set immutable identity constraints
        identity_context = set_identity_constraints(identity.agent_id, profile)

        # Track gate-in phase in self-model
        update_cognitive_state(
            processing_phase=ProcessingPhase.PRE_EXECUTION,
            current_task_description=spawn_request.objective,
        )

        # 4. T1: Ingest (any modality)
        modality_result = await ingest(raw_input, self._kit)
        modality_output = _extract_modality_output(modality_result)

        # Derive text for classification
        text = modality_output.cognitive_context or raw_input.content or ""

        # 5. T1: Classify signal
        classification_result = await classify(text, ClassProfileRules(), self._kit)
        classification = _extract_classification(classification_result)

        # 6. T1: Intent/Sentiment/Urgency
        labels_result = await run_primitive_scorers(text, self._kit)
        cognitive_labels = _extract_cognitive_labels(labels_result)

        # 7. T1: Entity Recognition (config-driven enablement)
        entities: list[ValidatedEntity] = []
        if get_settings().kernel.conscious_observer_expected_cycle_ms > 0:
            entities_result = await extract_entities(text, ValidatedEntity, self._kit)
            entities = _extract_entities(entities_result)

        # Build SignalTags from T1 outputs
        signal_tags = _build_signal_tags(
            classification, cognitive_labels, entities, modality_output
        )

        # 8. T6: Self-model capability assessment
        capability = await assess_capability(signal_tags, identity_context, self._kit)

        # Early return if not capable (caller checks .capability.can_handle)
        if not capability.can_handle:
            return GateInResult(
                identity_context=identity_context,
                signal_tags=signal_tags,
                modality_output=modality_output,
                classification=classification,
                cognitive_labels=cognitive_labels,
                entities=entities,
                activation_map=ActivationMap(
                    pipeline=None,
                    module_states={},
                    pressure_downgraded=False,
                    original_complexity=None,
                    cache_hit=False,
                ),
                capability=capability,
                mode=ProcessingMode.FAST,
                gate_in_duration_ms=(time.perf_counter() - start) * 1000,
            )

        # 9. T6: Compute activation map and pipeline mode
        activation_result = await compute_activation_map(
            signal_tags, capability, pressure=0.0, kit=self._kit
        )
        activation_map = _extract_activation_map(activation_result)
        mode = _complexity_to_mode(activation_map.pipeline.complexity_level)

        return GateInResult(
            identity_context=identity_context,
            signal_tags=signal_tags,
            modality_output=modality_output,
            classification=classification,
            cognitive_labels=cognitive_labels,
            entities=entities,
            activation_map=activation_map,
            capability=capability,
            mode=mode,
            gate_in_duration_ms=(time.perf_counter() - start) * 1000,
        )

    # ------------------------------------------------------------------
    # Phase 2: Execute (pipeline dispatcher)
    # ------------------------------------------------------------------

    async def _phase_execute(
        self,
        gate: GateInResult,
        spawn_request: SpawnRequest,
        rag_context: dict[str, Any] | None,
        trace_id: str,
    ) -> ObserverExecuteResult:
        """Dispatch to the correct pipeline branch based on ProcessingMode."""
        update_cognitive_state(
            processing_phase=ProcessingPhase.DURING_EXECUTION,
            current_task_description=spawn_request.objective,
        )

        if gate.mode == ProcessingMode.FAST:
            return await self._execute_fast_path(gate, spawn_request, rag_context)
        elif gate.mode == ProcessingMode.STANDARD:
            return await self._execute_standard_path(gate, spawn_request, rag_context)
        elif gate.mode == ProcessingMode.FULL:
            return await self._execute_full_path(gate, spawn_request, rag_context)
        else:  # EMERGENCY
            return await self._execute_emergency_path(gate, spawn_request, rag_context)

    # ------------------------------------------------------------------
    # Pipeline Branches
    # ------------------------------------------------------------------

    async def _execute_fast_path(
        self,
        gate: GateInResult,
        spawn_request: SpawnRequest,
        rag_context: dict[str, Any] | None,
    ) -> ObserverExecuteResult:
        """FAST: T1 + T4. For TRIVIAL/SIMPLE signals — no planning overhead."""
        start = time.perf_counter()
        agent_state = _build_agent_state(gate.identity_context, spawn_request)
        stm = ShortTermMemory()

        loop_result, decisions, outputs, simplified, escalated, aborted = (
            await self._run_ooda_with_clm(
                agent_state=agent_state,
                stm=stm,
                active_dag=None,
                objective=spawn_request.objective,
                activation_map=gate.activation_map,
                rag_context=rag_context,
                trace_id="",
            )
        )

        return ObserverExecuteResult(
            loop_result=loop_result,
            raw_artifact=_synthesize_artifact(loop_result),
            recent_decisions=decisions,
            recent_outputs=outputs,
            objective=spawn_request.objective,
            total_cycles=loop_result.total_cycles,
            was_simplified=simplified,
            was_escalated=escalated,
            was_aborted=aborted,
            execute_duration_ms=(time.perf_counter() - start) * 1000,
        )

    async def _execute_standard_path(
        self,
        gate: GateInResult,
        spawn_request: SpawnRequest,
        rag_context: dict[str, Any] | None,
    ) -> ObserverExecuteResult:
        """STANDARD: T2 decompose → T4. For MODERATE signals."""
        start = time.perf_counter()

        world_state = _build_world_state(spawn_request, gate.identity_context, rag_context)
        subtasks_result = await decompose_goal(world_state, self._kit)
        subtasks = _extract_subtasks(subtasks_result)

        agent_state = _build_agent_state(gate.identity_context, spawn_request)
        stm = ShortTermMemory()

        loop_result, decisions, outputs, simplified, escalated, aborted = (
            await self._run_ooda_with_clm(
                agent_state=agent_state,
                stm=stm,
                active_dag=None,
                objective=spawn_request.objective,
                activation_map=gate.activation_map,
                rag_context=rag_context,
                trace_id="",
            )
        )

        return ObserverExecuteResult(
            loop_result=loop_result,
            raw_artifact=_synthesize_artifact(loop_result),
            recent_decisions=decisions,
            recent_outputs=outputs,
            objective=spawn_request.objective,
            total_cycles=loop_result.total_cycles,
            was_simplified=simplified,
            was_escalated=escalated,
            was_aborted=aborted,
            execute_duration_ms=(time.perf_counter() - start) * 1000,
        )

    async def _execute_full_path(
        self,
        gate: GateInResult,
        spawn_request: SpawnRequest,
        rag_context: dict[str, Any] | None,
    ) -> ObserverExecuteResult:
        """FULL: T2 → T3 → T4. For COMPLEX signals — full DAG pipeline."""
        start = time.perf_counter()
        settings = get_settings().kernel

        # T2: Decompose goal
        world_state = _build_world_state(spawn_request, gate.identity_context, rag_context)
        decomp_result = await decompose_goal(world_state, self._kit)
        subtasks = _extract_subtasks(decomp_result)

        # T3: Synthesize DAG (delegates to Tier 2 What-If simulation internally)
        active_dag: ExecutableDAG | None = None
        if subtasks:
            plan_result = await synthesize_plan(
                objective=spawn_request.objective,
                context=world_state,
                kit=self._kit,
            )
            active_dag = _extract_dag(plan_result)

        # T3: Advanced planning (constraints from identity context)
        if active_dag and subtasks:
            constraints = PlanningConstraints(
                quality_bar=gate.identity_context.quality_bar,
                allowed_tools=list(gate.identity_context.tools_allowed),
                forbidden_actions=list(settings.guardrail_forbidden_actions),
            )
            # Hypotheses generation (tracked plan)
            plan_result = await plan_advanced(subtasks, constraints, self._kit)
            # In a full production implementation, hypotheses from plan_result 
            # would be injected into active_dag.state for OODA reflection.

        # T3: Pre-execution conscience gate
        if active_dag:
            pre_exec_result = await run_pre_execution_check(active_dag, self._kit)
            if not pre_exec_result.error and pre_exec_result.signals:
                approval = pre_exec_result.signals[0].body["data"]
                if approval.get("decision") == "rejected":
                    # Guardrails blocked execution
                    return ObserverExecuteResult(
                        loop_result=LoopResult(
                            agent_id=gate.identity_context.agent_id,
                            total_cycles=0,
                            termination_reason=LoopTerminationReason.LIFECYCLE_SIGNAL,
                            final_state=_build_agent_state(gate.identity_context, spawn_request).model_dump(),
                            total_duration_ms=0.0,
                            total_cost=0.0,
                            objectives_completed=[],
                            artifacts_produced=["Execution blocked by pre-execution guardrails"],
                        ),
                        raw_artifact=approval.get("reasoning", "Rejected by guardrails"),
                        recent_decisions=[],
                        recent_outputs=[],
                        objective=spawn_request.objective,
                        total_cycles=0,
                        was_simplified=False,
                        was_escalated=True,
                        was_aborted=False,
                        execute_duration_ms=(time.perf_counter() - start) * 1000,
                    )

        # T4: OODA loop with CLM monitoring
        agent_state = _build_agent_state(gate.identity_context, spawn_request)
        if active_dag:
            agent_state.active_dag_id = active_dag.dag_id

        stm = ShortTermMemory()

        loop_result, decisions, outputs, simplified, escalated, aborted = (
            await self._run_ooda_with_clm(
                agent_state=agent_state,
                stm=stm,
                active_dag=active_dag,
                objective=spawn_request.objective,
                activation_map=gate.activation_map,
                rag_context=rag_context,
                trace_id="",
            )
        )

        return ObserverExecuteResult(
            loop_result=loop_result,
            raw_artifact=_synthesize_artifact(loop_result),
            recent_decisions=decisions,
            recent_outputs=outputs,
            objective=spawn_request.objective,
            total_cycles=loop_result.total_cycles,
            was_simplified=simplified,
            was_escalated=escalated,
            was_aborted=aborted,
            execute_duration_ms=(time.perf_counter() - start) * 1000,
        )

    async def _execute_emergency_path(
        self,
        gate: GateInResult,
        spawn_request: SpawnRequest,
        rag_context: dict[str, Any] | None,
    ) -> ObserverExecuteResult:
        """EMERGENCY: T4 (capped cycles). For CRITICAL signals — no planning."""
        start = time.perf_counter()
        settings = get_settings().kernel
        max_cycles = settings.conscious_observer_emergency_max_cycles

        agent_state = _build_agent_state(gate.identity_context, spawn_request)
        stm = ShortTermMemory()

        loop_result, decisions, outputs, simplified, escalated, aborted = (
            await self._run_ooda_with_clm(
                agent_state=agent_state,
                stm=stm,
                active_dag=None,
                objective=spawn_request.objective,
                activation_map=gate.activation_map,
                rag_context=rag_context,
                trace_id="",
                max_cycles_override=max_cycles,
            )
        )

        return ObserverExecuteResult(
            loop_result=loop_result,
            raw_artifact=_synthesize_artifact(loop_result),
            recent_decisions=decisions,
            recent_outputs=outputs,
            objective=spawn_request.objective,
            total_cycles=loop_result.total_cycles,
            was_simplified=False,
            was_escalated=escalated,
            was_aborted=aborted,
            execute_duration_ms=(time.perf_counter() - start) * 1000,
        )

    # ------------------------------------------------------------------
    # Core CLM Monitoring Loop — The Heart of Tier 7
    # ------------------------------------------------------------------

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
        """Run OODA cycles with Cognitive Load Monitor intercept after every cycle.

        Unlike run_ooda_loop(), which runs autonomously, this loop gives Tier 7
        full executive control: CLM can SIMPLIFY, ESCALATE, or ABORT mid-execution
        — the metacognitive equivalent of a human realising they're going in circles.

        Returns:
            (loop_result, recent_decisions, recent_outputs,
             was_simplified, was_escalated, was_aborted)
        """
        settings = get_settings().kernel
        max_cycles = max_cycles_override or settings.ooda_max_cycles
        expected_ms = settings.conscious_observer_expected_cycle_ms
        max_simplify = settings.conscious_observer_simplify_max_steps

        state = agent_state
        all_artifacts: list[str] = []
        recent_decisions: list[Decision] = []
        recent_outputs: list[str] = []
        completed_objectives: list[str] = []
        termination_reason = LoopTerminationReason.MAX_CYCLES_REACHED

        was_simplified = False
        was_escalated = False
        was_aborted = False
        simplify_steps_used = 0
        current_activation_map = activation_map

        start_loop = time.perf_counter()

        for cycle_num in range(max_cycles):
            if state.status in (AgentStatus.SLEEPING, AgentStatus.TERMINATED):
                termination_reason = LoopTerminationReason.LIFECYCLE_SIGNAL
                break

            cycle_start = time.perf_counter()

            # Run one OODA cycle
            cycle_result = await run_ooda_cycle(
                state=state,
                stm=stm,
                active_dag=active_dag,
                rag_context=rag_context,
                kit=self._kit,
            )

            cycle_ms = (time.perf_counter() - cycle_start) * 1000
            all_artifacts.extend(cycle_result.artifacts_produced)

            # Accumulate recent context for CLM and Gate-Out
            if cycle_result.action_results:
                for ar in cycle_result.action_results:
                    if ar.outputs:
                        summary = "; ".join(f"{k}={v}" for k, v in list(ar.outputs.items())[:3])
                        recent_outputs.append(summary)

            # Recover last decision from state snapshot
            agent_status = cycle_result.state_snapshot.get("status", "active")
            
            # Map AgentStatus to DecisionAction for CLM monitoring
            if agent_status == AgentStatus.ACTIVE:
                action = DecisionAction.CONTINUE
            elif agent_status in (AgentStatus.BLOCKED, AgentStatus.PARKED):
                action = DecisionAction.PARK
            elif agent_status == AgentStatus.SLEEPING:
                action = DecisionAction.SLEEP
            elif agent_status == AgentStatus.TERMINATED:
                action = DecisionAction.COMPLETE
            else:
                action = DecisionAction.CONTINUE

            recent_decisions.append(
                Decision(
                    action=action,
                    reasoning=f"cycle {cycle_num + 1}",
                )
            )

            # T6: Cognitive Load Monitor after every cycle
            active_module_count = 0
            for v in current_activation_map.module_states.values():
                val = getattr(v, "value", str(v))
                if val == "active" or str(v).endswith("active"):
                    active_module_count += 1
            telemetry = CycleTelemetry(
                cycle_number=cycle_num,
                tokens_consumed=0,
                cycle_duration_ms=cycle_ms,
                expected_duration_ms=expected_ms,
                active_module_count=active_module_count,
                total_cycles_budget=max_cycles,
                total_tokens_budget=settings.budget_epoch_token_limit,
            )

            clm_result = await monitor_cognitive_load(
                activation_map=current_activation_map,
                telemetry=telemetry,
                recent_decisions=recent_decisions,
                recent_outputs=recent_outputs or None,
                original_objective=objective,
                kit=self._kit,
            )

            if not clm_result.error and clm_result.signals:
                recommendation = _extract_load_recommendation(clm_result)

                if recommendation.action == LoadAction.ABORT:
                    log.warning(
                        "CLM: ABORT — terminating loop",
                        cycle=cycle_num,
                        reasoning=recommendation.reasoning,
                    )
                    was_aborted = True
                    termination_reason = LoopTerminationReason.LIFECYCLE_SIGNAL
                    break

                elif recommendation.action == LoadAction.ESCALATE:
                    log.warning(
                        "CLM: ESCALATE — breaking loop early",
                        cycle=cycle_num,
                        reasoning=recommendation.reasoning,
                    )
                    was_escalated = True
                    termination_reason = LoopTerminationReason.LIFECYCLE_SIGNAL
                    break

                elif recommendation.action == LoadAction.SIMPLIFY:
                    if simplify_steps_used < max_simplify:
                        current_activation_map = _downgrade_activation_map(
                            current_activation_map
                        )
                        simplify_steps_used += 1
                        was_simplified = True
                        log.info(
                            "CLM: SIMPLIFY — pipeline downgraded",
                            cycle=cycle_num,
                            steps_used=simplify_steps_used,
                            new_pipeline=current_activation_map.pipeline.pipeline_name
                            if current_activation_map.pipeline else "unknown",
                        )
                    # If max simplify steps reached, continue at current level

            # Check natural OODA cycle completion
            if cycle_result.next_action == CycleAction.TERMINATE:
                termination_reason = LoopTerminationReason.OBJECTIVE_COMPLETE
                completed_objectives = [
                    obj.objective_id
                    for obj in state.current_objectives
                    if obj.completed
                ]
                break

            elif cycle_result.next_action in (CycleAction.PARK, CycleAction.SLEEP):
                termination_reason = LoopTerminationReason.ALL_DAGS_PARKED
                break

        elapsed_loop = (time.perf_counter() - start_loop) * 1000

        loop_result = LoopResult(
            agent_id=state.agent_id,
            total_cycles=state.cycle_count,
            termination_reason=termination_reason,
            final_state=state.model_dump(),
            total_duration_ms=elapsed_loop,
            total_cost=state.total_cost,
            objectives_completed=completed_objectives,
            artifacts_produced=all_artifacts,
        )

        log.info(
            "OODA+CLM loop complete",
            agent_id=state.agent_id,
            cycles=state.cycle_count,
            reason=termination_reason.value,
            simplified=was_simplified,
            escalated=was_escalated,
            aborted=was_aborted,
            duration_ms=round(elapsed_loop, 2),
        )

        return (
            loop_result,
            recent_decisions,
            recent_outputs,
            was_simplified,
            was_escalated,
            was_aborted,
        )

    # ------------------------------------------------------------------
    # Phase 3: Gate-Out
    # ------------------------------------------------------------------

    async def _phase_gate_out(
        self,
        gate: GateInResult,
        exec_res: ObserverExecuteResult,
        evidence: list[Origin],
        trace_id: str,
        gate_in_ms: float,
        execute_ms: float,
        start_total: float,
    ) -> ConsciousObserverResult:
        """T6 quality chain: grounding → confidence → noise gate → retry.

        Steps:
            1. Build ToolOutput from loop artifacts
            2. T6 Hallucination Monitor — verify epistemic grounding
            3. T6 Confidence Calibrator — align confidence with accuracy history
            4. T6 Noise Gate — pass or reject; retry if budget allows
        """
        update_cognitive_state(processing_phase=ProcessingPhase.POST_EXECUTION)

        elapsed_total = (time.perf_counter() - start_total) * 1000

        # Short-circuit if execution was escalated or aborted
        if exec_res.was_escalated or exec_res.was_aborted:
            phase = ObserverPhase.ABORTED if exec_res.was_aborted else ObserverPhase.ESCALATED
            return ConsciousObserverResult(
                trace_id=trace_id,
                agent_id=exec_res.loop_result.agent_id,
                mode=gate.mode,
                final_phase=phase,
                partial_output=exec_res.raw_artifact,
                total_duration_ms=elapsed_total,
                total_cycles=exec_res.total_cycles,
                gate_in_ms=gate_in_ms,
                execute_ms=execute_ms,
                gate_out_ms=0.0,
                was_simplified=exec_res.was_simplified,
                was_escalated=exec_res.was_escalated,
                was_aborted=exec_res.was_aborted,
            )

        settings = get_settings().kernel
        quality_bar = gate.identity_context.quality_bar

        # Build ToolOutput for noise gate
        tool_output = _build_tool_output(exec_res.loop_result, trace_id)

        # T6: Hallucination Monitor
        grounding: GroundingReport | None = None
        if evidence:
            grounding_result = await verify_grounding(tool_output, evidence, self._kit)
            if not grounding_result.error and grounding_result.signals:
                grounding = _extract_grounding_report(grounding_result)

        grounding_score = grounding.grounding_score if grounding else 0.8

        # T6: Confidence Calibrator
        history = get_calibration_history()
        domain = gate.signal_tags.domain
        confidence_result = await run_confidence_calibration(
            stated_confidence=gate.capability.confidence,
            grounding_score=grounding_score,
            history=history,
            domain=domain,
        )
        calibrated_confidence: CalibratedConfidence | None = None
        if not confidence_result.error and confidence_result.signals:
            calibrated_confidence = _extract_calibrated_confidence(confidence_result)

        # T6: Noise Gate
        gate_result = await filter_output(
            output=tool_output,
            grounding=grounding or _empty_grounding_report(tool_output.output_id),
            confidence=calibrated_confidence or _default_confidence(),
            quality_bar_override=quality_bar,
        )
        verdict = _extract_filter_result(gate_result)

        elapsed_total = (time.perf_counter() - start_total) * 1000

        if isinstance(verdict, FilteredOutput):
            # PASS — clean up retry counter and return success
            clear_retry_budget(tool_output.output_id)
            return ConsciousObserverResult(
                trace_id=trace_id,
                agent_id=exec_res.loop_result.agent_id,
                mode=gate.mode,
                final_phase=ObserverPhase.GATE_OUT,
                filtered_output=verdict,
                grounding_report=grounding,
                calibrated_confidence=calibrated_confidence,
                total_duration_ms=elapsed_total,
                total_cycles=exec_res.total_cycles,
                gate_in_ms=gate_in_ms,
                execute_ms=execute_ms,
                gate_out_ms=elapsed_total - gate_in_ms - execute_ms,
                was_simplified=exec_res.was_simplified,
                was_escalated=exec_res.was_escalated,
                was_aborted=exec_res.was_aborted,
            )

        # REJECT — check retry budget from guidance
        guidance = verdict.guidance
        if not guidance.should_escalate:
            log.info(
                "Noise gate rejected — retry budget available",
                output_id=tool_output.output_id,
                retries_used=guidance.retry_count,
                reason=guidance.rejection_reason,
            )

        # Budget exhausted or escalation — return partial output with guidance
        return ConsciousObserverResult(
            trace_id=trace_id,
            agent_id=exec_res.loop_result.agent_id,
            mode=gate.mode,
            final_phase=ObserverPhase.ESCALATED if guidance.should_escalate else ObserverPhase.GATE_OUT,
            partial_output=exec_res.raw_artifact,
            escalation_guidance=guidance,
            grounding_report=grounding,
            calibrated_confidence=calibrated_confidence,
            total_duration_ms=elapsed_total,
            total_cycles=exec_res.total_cycles,
            gate_in_ms=gate_in_ms,
            execute_ms=execute_ms,
            gate_out_ms=elapsed_total - gate_in_ms - execute_ms,
            was_simplified=exec_res.was_simplified,
            was_escalated=exec_res.was_escalated or guidance.should_escalate,
            was_aborted=exec_res.was_aborted,
        )


# ============================================================================
# Stub Fallbacks for Gate-Out When Upstream Modules Produce No Output
# ============================================================================


def _empty_grounding_report(output_id: str) -> GroundingReport:
    """Produce a neutral GroundingReport when the monitor returns no result."""
    from kernel.hallucination_monitor.types import GroundingReport

    return GroundingReport(
        output_id=output_id,
        total_claims=0,
        grounded_count=0,
        inferred_count=0,
        fabricated_count=0,
        claim_grades=[],
        grounding_score=0.8,
    )


def _default_confidence() -> CalibratedConfidence:
    """Produce a neutral CalibratedConfidence when calibrator returns no result."""
    return CalibratedConfidence(
        stated_confidence=0.8,
        calibrated_confidence=0.8,
        correction_factor=1.0,
        is_overconfident=False,
        is_underconfident=False,
        domain="general",
    )


# ============================================================================
# Module-Level Entry Point — matches Signal → Result protocol
# ============================================================================


async def run_conscious_observer(
    raw_input: RawInput,
    spawn_request: SpawnRequest,
    kit: InferenceKit | None = None,
    evidence: list[Origin] | None = None,
    rag_context: dict[str, Any] | None = None,
    trace_id: str = "",
) -> Result:
    """Module-level entry point for the Tier 7 Conscious Observer.

    Convenience wrapper around ConsciousObserver.process() for callers
    that prefer a pure function interface over instantiating the class.

    Args:
        raw_input:      Any modality — text, audio, image, video, or document.
        spawn_request:  Corporate Kernel directive (role, objective, budgets).
        kit:            Inference kit for LLM / embedder access.
        evidence:       Optional external evidence for Gate-Out grounding.
        rag_context:    Optional RAG-enriched context for OODA orientation.
        trace_id:       Propagated trace ID (auto-generated if empty).

    Returns:
        Result containing ConsciousObserverResult in signals[0].data.
    """
    observer = ConsciousObserver(kit=kit)
    return await observer.process(
        raw_input=raw_input,
        spawn_request=spawn_request,
        evidence=evidence,
        rag_context=rag_context,
        trace_id=trace_id,
    )
