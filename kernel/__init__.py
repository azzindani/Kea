"""
Kea Human Kernel — Core Processing, Cognitive Engines, Orchestration & Execution.

The kernel implements the Layered Pyramid Architecture, modeled after the
Linux kernel's modular subsystem design. Each tier provides a clear interface
boundary, and lower tiers never depend on upper tiers.

Tier Structure (implemented modules)::

    Tier 0: Base Foundation              → shared/ (schemas, standard_io, config)
    Tier 1: Core Processing (kernel/)    → Classification, NER, Validation, Scoring, etc.
    Tier 2: Cognitive Engines (kernel/)  → Task Decomposition, Curiosity, What-If, Attention
    Tier 3: Complex Orchestration (kernel/) → Graph Synthesizer, Node Assembler, Planning, Guardrails
    Tier 4: Execution Engine (kernel/)   → OODA Loop, Async Multitasking, Short-Term Memory

    Tier 5: Autonomous Ego (kernel/)    → Lifecycle Controller, Energy & Interrupts
    Tier 6: Conscious Observer (kernel/) → Self Model, Activation Router, Load Monitor,
                                           Hallucination Monitor, Confidence Calibrator, Noise Gate

Tier 1 — Core Processing Primitives:
    classification/             Signal classification via linguistic + semantic + hybrid merge
    intent_sentiment_urgency/   Parallel intent/sentiment/urgency primitive scorers
    entity_recognition/         Named entity recognition with schema-based validation
    validation/                 Four-gate data validation cascade (Syntax→Structure→Types→Bounds)
    scoring/                    Three-track hybrid evaluation (Semantic+Precision+Reward)
    modality/                   Omni-modal ingestion and demuxing (text/audio/image/video/doc)
    location_and_time/          Spatiotemporal anchoring (resolves "where" and "when")

Tier 2 — Cognitive Engines:
    task_decomposition/         Goal decomposition into sub-tasks with dependency graphs
    curiosity_engine/           Knowledge gap detection and exploration strategy routing
    what_if_scenario/           Offline counter-factual simulation and risk/reward analysis
    attention_and_plausibility/ Attention filtering and plausibility/sanity checking

Tier 3 — Complex Orchestration:
    graph_synthesizer/          JIT DAG compilation from Tier 2 sub-tasks
    node_assembler/             Factory for executable DAG nodes with validation layers
    advanced_planning/          Sequencing, tool binding, hypothesis generation, progress tracking
    reflection_and_guardrails/  Pre-execution conscience gates and post-execution optimization

Tier 4 — Execution Engine:
    ooda_loop/                  Observe-Orient-Decide-Act continuous execution cycle
    async_multitasking/         DAG parking, context switching, deep sleep delegation
    short_term_memory/          Ephemeral RAM: event history, entity cache, DAG state tracking

Tier 5 — Autonomous Ego:
    lifecycle_controller/       Agent genesis, identity, sleep/wake/panic, epoch memory
    energy_and_interrupts/      Budget tracking, exhaustion detection, corporate interrupts

Tier 6 — Conscious Observer (Metacognitive Oversight):
    self_model/                 Capability maps, cognitive state, accuracy tracking
    activation_router/          Selective module activation, pipeline selection, pressure adaptation
    cognitive_load_monitor/     Load measurement, loop/stall/oscillation/drift detection
    hallucination_monitor/      Claim extraction, grading (GROUNDED/INFERRED/FABRICATED)
    confidence_calibrator/      Domain-specific calibration curves, overconfidence detection
    noise_gate/                 Final quality checkpoint, rejection with retry guidance

Integration Protocol:
    - All functions accept Signal(s) and return Result
    - All errors are KernelError (first-class data, not exceptions)
    - All config flows from shared.config.get_settings().kernel
    - All logging uses shared.logging.main.get_logger(__name__)
    - Tier N modules call Tier N-1 primitives; never the reverse
    - Tier-to-module mapping is documented in redesign/ specs

Directory naming uses MODULE NAMES, not tier numbers.
"""

from __future__ import annotations

from kernel.activation_router import (
    ActivationMap,
    ComplexityLevel,
    ModuleActivation,
    PipelineConfig,
    cache_decision,
    check_decision_cache,
    classify_signal_complexity,
    compute_activation_map,
    select_pipeline,
)
from kernel.advanced_planning import (
    ExpectedOutcome,
    PlanningConstraints,
    PriorityMode,
    ProgressTracker,
    TrackedPlan,
    bind_tools,
    generate_hypotheses,
    inject_progress_tracker,
    plan_advanced,
    sequence_and_prioritize,
)
from kernel.async_multitasking import (
    DAGQueue,
    NextAction,
    NextActionKind,
    ParkingTicket,
    SleepToken,
    WaitHandle,
    check_async_requirement,
    manage_async_tasks,
    park_dag_state,
    request_deep_sleep,
    switch_context,
)
from kernel.attention_and_plausibility import (
    RefinedState,
    SanityAlert,
    TaskState,
    run_cognitive_filters,
)

# ============================================================================
# Tier 1: Core Processing Primitives
# ============================================================================
from kernel.classification import (
    ClassificationResult,
    ClassProfileRules,
    FallbackTrigger,
    classify,
)
from kernel.cognitive_load_monitor import (
    CognitiveLoad,
    CycleTelemetry,
    GoalDriftDetection,
    LoadAction,
    LoadRecommendation,
    LoopDetection,
    OscillationDetection,
    detect_goal_drift,
    detect_loop,
    detect_oscillation,
    detect_stall,
    measure_load,
    monitor_cognitive_load,
    recommend_action,
)
from kernel.confidence_calibrator import (
    CalibratedConfidence,
    calibrate_confidence,
    detect_overconfidence,
    detect_underconfidence,
    get_calibration_curve,
    run_confidence_calibration,
    update_calibration_curve,
)
from kernel.curiosity_engine import (
    ExplorationTask,
    explore_gaps,
)
from kernel.energy_and_interrupts import (
    BudgetState,
    ControlAction,
    ControlDecision,
    ControlTrigger,
    ControlTriggerSource,
    CostDimension,
    CostEvent,
    InterruptAction,
    InterruptSignal,
    InterruptType,
    LifecycleTransition,
    check_budget_exhaustion,
    check_budget_warning,
    enforce_energy_authority,
    handle_interrupt,
    manage_lifecycle_state,
    track_budget,
)
from kernel.entity_recognition import (
    ValidatedEntity,
    extract_entities,
)

# ============================================================================
# Tier 3: Complex Orchestration
# ============================================================================
from kernel.graph_synthesizer import (
    ActionInstruction,
    Edge,
    EdgeKind,
    ExecutableDAG,
    ExecutableNode,
    calculate_dependency_edges,
    compile_dag,
    map_subtasks_to_nodes,
    synthesize_plan,
)
from kernel.hallucination_monitor import (
    Claim,
    ClaimGrade,
    ClaimGradeLevel,
    ClaimType,
    EvidenceLink,
    GroundingReport,
    Origin,
    calculate_grounding_score,
    classify_claims,
    grade_claim,
    trace_evidence_chain,
    verify_grounding,
)
from kernel.intent_sentiment_urgency import (
    CognitiveLabels,
    IntentLabel,
    SentimentLabel,
    UrgencyLabel,
    analyze_sentiment,
    detect_intent,
    run_primitive_scorers,
    score_urgency,
)

# ============================================================================
# Tier 5: Autonomous Ego
# ============================================================================
from kernel.lifecycle_controller import (
    AgentIdentity,
    AgentLifecycle,
    CognitiveProfile,
    IdentityContext,
    LifecyclePhase,
    LifecycleSignal,
    LifecycleSignalType,
    LifecycleState,
    ObjectiveState,
    ObjectiveStatus,
    SpawnRequest,
    commit_epoch_memory,
    control_sleep_wake,
    initialize_agent,
    load_cognitive_profile,
    run_lifecycle,
    set_identity_constraints,
    track_macro_objective,
)
from kernel.location_and_time import (
    SpatiotemporalBlock,
    anchor_spatiotemporal,
)
from kernel.modality import (
    ModalityOutput,
    RawInput,
    ingest,
)
from kernel.node_assembler import (
    AssemblyConfig,
    AssemblyReport,
    assemble_node,
    hook_input_validation,
    hook_output_validation,
    inject_telemetry,
    wrap_in_standard_io,
)
from kernel.noise_gate import (
    FilteredOutput,
    QualityMetadata,
    RejectedOutput,
    RejectionDimension,
    RetryBudgetStatus,
    RetryGuidance,
    ToolOutput,
    annotate_output,
    apply_quality_threshold,
    check_retry_budget,
    clear_retry_budget,
    filter_output,
    generate_rejection_feedback,
)

# ============================================================================
# Tier 4: Execution Engine
# ============================================================================
from kernel.ooda_loop import (
    ActionResult,
    AgentState,
    AgentStatus,
    CycleAction,
    CycleResult,
    Decision,
    DecisionAction,
    EventStream,
    LoopResult,
    LoopTerminationReason,
    MacroObjective,
    OrientedState,
    act,
    decide,
    observe,
    orient,
    run_ooda_cycle,
    run_ooda_loop,
)
from kernel.reflection_and_guardrails import (
    ApprovalDecision,
    ApprovalResult,
    CritiqueReport,
    ExecutionResult,
    GuardrailResult,
    OptimizationSuggestion,
    ReflectionInsight,
    check_value_guardrails,
    critique_execution,
    evaluate_consensus,
    optimize_loop,
    run_post_execution_reflection,
    run_pre_execution_check,
)
from kernel.scoring import (
    Constraint,
    NumericScore,
    score,
)

# ============================================================================
# Tier 6: Conscious Observer (Metacognitive Oversight)
# ============================================================================
from kernel.self_model import (
    AgentCognitiveState,
    CalibrationCurve,
    CalibrationDataPoint,
    CalibrationHistory,
    CapabilityAssessment,
    CapabilityGap,
    ProcessingPhase,
    SignalTags,
    assess_capability,
    detect_capability_gap,
    get_calibration_history,
    get_current_state,
    refresh_capability_map,
    run_self_model,
    update_accuracy_history,
    update_cognitive_state,
)
from kernel.short_term_memory import (
    ContextSlice,
    DagStateSnapshot,
    EpochSummary,
    EventSource,
    NodeExecutionStatus,
    ObservationEvent,
    ShortTermMemory,
)

# ============================================================================
# Tier 2: Cognitive Engines
# ============================================================================
from kernel.task_decomposition import (
    SubTaskItem,
    WorldState,
    decompose_goal,
)
from kernel.validation import (
    ErrorResponse,
    SuccessResult,
    validate,
)
from kernel.what_if_scenario import (
    CompiledDAG,
    SimulationVerdict,
    simulate_outcomes,
)

__all__ = [
    # --- Tier 1: Core Processing ---
    # Classification
    "classify",
    "ClassificationResult",
    "ClassProfileRules",
    "FallbackTrigger",
    # Intent / Sentiment / Urgency
    "run_primitive_scorers",
    "detect_intent",
    "analyze_sentiment",
    "score_urgency",
    "CognitiveLabels",
    "IntentLabel",
    "SentimentLabel",
    "UrgencyLabel",
    # Entity Recognition
    "extract_entities",
    "ValidatedEntity",
    # Validation
    "validate",
    "SuccessResult",
    "ErrorResponse",
    # Scoring
    "score",
    "NumericScore",
    "Constraint",
    # Modality
    "ingest",
    "ModalityOutput",
    "RawInput",
    # Location & Time
    "anchor_spatiotemporal",
    "SpatiotemporalBlock",
    # --- Tier 2: Cognitive Engines ---
    # Task Decomposition
    "decompose_goal",
    "WorldState",
    "SubTaskItem",
    # Curiosity Engine
    "explore_gaps",
    "ExplorationTask",
    # What-If Scenario
    "simulate_outcomes",
    "SimulationVerdict",
    "CompiledDAG",
    # Attention & Plausibility
    "run_cognitive_filters",
    "RefinedState",
    "SanityAlert",
    "TaskState",
    # --- Tier 3: Complex Orchestration ---
    # Graph Synthesizer
    "synthesize_plan",
    "map_subtasks_to_nodes",
    "calculate_dependency_edges",
    "compile_dag",
    "ExecutableDAG",
    "ExecutableNode",
    "ActionInstruction",
    "Edge",
    "EdgeKind",
    # Node Assembler
    "assemble_node",
    "wrap_in_standard_io",
    "inject_telemetry",
    "hook_input_validation",
    "hook_output_validation",
    "AssemblyConfig",
    "AssemblyReport",
    # Advanced Planning
    "plan_advanced",
    "sequence_and_prioritize",
    "bind_tools",
    "generate_hypotheses",
    "inject_progress_tracker",
    "TrackedPlan",
    "PlanningConstraints",
    "PriorityMode",
    "ExpectedOutcome",
    "ProgressTracker",
    # Reflection & Guardrails
    "run_pre_execution_check",
    "run_post_execution_reflection",
    "evaluate_consensus",
    "check_value_guardrails",
    "critique_execution",
    "optimize_loop",
    "ApprovalResult",
    "ApprovalDecision",
    "GuardrailResult",
    "ExecutionResult",
    "CritiqueReport",
    "ReflectionInsight",
    "OptimizationSuggestion",
    # --- Tier 4: Execution Engine ---
    # OODA Loop
    "run_ooda_loop",
    "run_ooda_cycle",
    "observe",
    "orient",
    "decide",
    "act",
    "AgentState",
    "AgentStatus",
    "MacroObjective",
    "Decision",
    "DecisionAction",
    "ActionResult",
    "CycleResult",
    "CycleAction",
    "LoopResult",
    "LoopTerminationReason",
    "OrientedState",
    "EventStream",
    # Async Multitasking
    "manage_async_tasks",
    "check_async_requirement",
    "park_dag_state",
    "switch_context",
    "request_deep_sleep",
    "DAGQueue",
    "NextAction",
    "NextActionKind",
    "ParkingTicket",
    "SleepToken",
    "WaitHandle",
    # Short-Term Memory
    "ShortTermMemory",
    "ObservationEvent",
    "EventSource",
    "DagStateSnapshot",
    "NodeExecutionStatus",
    "ContextSlice",
    "EpochSummary",
    # --- Tier 5: Autonomous Ego ---
    # Lifecycle Controller
    "run_lifecycle",
    "initialize_agent",
    "load_cognitive_profile",
    "set_identity_constraints",
    "track_macro_objective",
    "control_sleep_wake",
    "commit_epoch_memory",
    "SpawnRequest",
    "AgentIdentity",
    "CognitiveProfile",
    "IdentityContext",
    "LifecyclePhase",
    "LifecycleSignal",
    "LifecycleSignalType",
    "LifecycleState",
    "ObjectiveState",
    "ObjectiveStatus",
    "AgentLifecycle",
    # Energy & Interrupts
    "enforce_energy_authority",
    "track_budget",
    "check_budget_exhaustion",
    "check_budget_warning",
    "handle_interrupt",
    "manage_lifecycle_state",
    "CostDimension",
    "CostEvent",
    "BudgetState",
    "InterruptType",
    "InterruptSignal",
    "InterruptAction",
    "ControlTriggerSource",
    "ControlTrigger",
    "LifecycleTransition",
    "ControlAction",
    "ControlDecision",
    # --- Tier 6: Conscious Observer ---
    # Self Model
    "run_self_model",
    "assess_capability",
    "get_current_state",
    "update_cognitive_state",
    "update_accuracy_history",
    "get_calibration_history",
    "detect_capability_gap",
    "refresh_capability_map",
    "SignalTags",
    "CapabilityGap",
    "CapabilityAssessment",
    "ProcessingPhase",
    "AgentCognitiveState",
    "CalibrationDataPoint",
    "CalibrationHistory",
    "CalibrationCurve",
    # Activation Router
    "compute_activation_map",
    "classify_signal_complexity",
    "select_pipeline",
    "check_decision_cache",
    "cache_decision",
    "ComplexityLevel",
    "ModuleActivation",
    "PipelineConfig",
    "ActivationMap",
    # Cognitive Load Monitor
    "monitor_cognitive_load",
    "measure_load",
    "detect_loop",
    "detect_stall",
    "detect_oscillation",
    "detect_goal_drift",
    "recommend_action",
    "CycleTelemetry",
    "CognitiveLoad",
    "LoopDetection",
    "OscillationDetection",
    "GoalDriftDetection",
    "LoadAction",
    "LoadRecommendation",
    # Hallucination Monitor
    "verify_grounding",
    "classify_claims",
    "grade_claim",
    "calculate_grounding_score",
    "trace_evidence_chain",
    "ClaimType",
    "Claim",
    "Origin",
    "EvidenceLink",
    "ClaimGradeLevel",
    "ClaimGrade",
    "GroundingReport",
    # Confidence Calibrator
    "run_confidence_calibration",
    "calibrate_confidence",
    "detect_overconfidence",
    "detect_underconfidence",
    "update_calibration_curve",
    "get_calibration_curve",
    "CalibratedConfidence",
    # Noise Gate
    "filter_output",
    "apply_quality_threshold",
    "annotate_output",
    "generate_rejection_feedback",
    "check_retry_budget",
    "clear_retry_budget",
    "ToolOutput",
    "QualityMetadata",
    "FilteredOutput",
    "RejectedOutput",
    "RejectionDimension",
    "RetryGuidance",
    "RetryBudgetStatus",
]
