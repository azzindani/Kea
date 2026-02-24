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

    Tier 5+: Future tiers (lifecycle, observer, corporate kernel)

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

# ============================================================================
# Tier 1: Core Processing Primitives
# ============================================================================

from kernel.classification import (
    classify,
    ClassificationResult,
    ClassProfileRules,
    FallbackTrigger,
)

from kernel.intent_sentiment_urgency import (
    run_primitive_scorers,
    detect_intent,
    analyze_sentiment,
    score_urgency,
    CognitiveLabels,
    IntentLabel,
    SentimentLabel,
    UrgencyLabel,
)

from kernel.entity_recognition import (
    extract_entities,
    ValidatedEntity,
)

from kernel.validation import (
    validate,
    SuccessResult,
    ErrorResponse,
)

from kernel.scoring import (
    score,
    NumericScore,
    Constraint,
)

from kernel.modality import (
    ingest,
    ModalityOutput,
    RawInput,
)

from kernel.location_and_time import (
    anchor_spatiotemporal,
    SpatiotemporalBlock,
)

# ============================================================================
# Tier 2: Cognitive Engines
# ============================================================================

from kernel.task_decomposition import (
    decompose_goal,
    WorldState,
    SubTaskItem,
)

from kernel.curiosity_engine import (
    explore_gaps,
    ExplorationTask,
)

from kernel.what_if_scenario import (
    simulate_outcomes,
    SimulationVerdict,
    CompiledDAG,
)

from kernel.attention_and_plausibility import (
    run_cognitive_filters,
    RefinedState,
    SanityAlert,
    TaskState,
)

# ============================================================================
# Tier 3: Complex Orchestration
# ============================================================================

from kernel.graph_synthesizer import (
    synthesize_plan,
    map_subtasks_to_nodes,
    calculate_dependency_edges,
    compile_dag,
    ExecutableDAG,
    ExecutableNode,
    ActionInstruction,
    Edge,
    EdgeKind,
)

from kernel.node_assembler import (
    assemble_node,
    wrap_in_standard_io,
    inject_telemetry,
    hook_input_validation,
    hook_output_validation,
    AssemblyConfig,
    AssemblyReport,
)

from kernel.advanced_planning import (
    plan_advanced,
    sequence_and_prioritize,
    bind_tools,
    generate_hypotheses,
    inject_progress_tracker,
    TrackedPlan,
    PlanningConstraints,
    PriorityMode,
    ExpectedOutcome,
    ProgressTracker,
)

from kernel.reflection_and_guardrails import (
    run_pre_execution_check,
    run_post_execution_reflection,
    evaluate_consensus,
    check_value_guardrails,
    critique_execution,
    optimize_loop,
    ApprovalResult,
    ApprovalDecision,
    GuardrailResult,
    ExecutionResult,
    CritiqueReport,
    ReflectionInsight,
    OptimizationSuggestion,
)

# ============================================================================
# Tier 4: Execution Engine
# ============================================================================

from kernel.ooda_loop import (
    run_ooda_loop,
    run_ooda_cycle,
    observe,
    orient,
    decide,
    act,
    AgentState,
    AgentStatus,
    MacroObjective,
    Decision,
    DecisionAction,
    ActionResult,
    CycleResult,
    CycleAction,
    LoopResult,
    LoopTerminationReason,
    OrientedState,
    EventStream,
)

from kernel.async_multitasking import (
    manage_async_tasks,
    check_async_requirement,
    park_dag_state,
    switch_context,
    request_deep_sleep,
    DAGQueue,
    NextAction,
    NextActionKind,
    ParkingTicket,
    SleepToken,
    WaitHandle,
)

from kernel.short_term_memory import (
    ShortTermMemory,
    ObservationEvent,
    EventSource,
    DagStateSnapshot,
    NodeExecutionStatus,
    ContextSlice,
    EpochSummary,
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
]
