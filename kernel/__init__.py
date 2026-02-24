"""
Kea Human Kernel — Core Processing and Cognitive Engines.

The kernel implements the Layered Pyramid Architecture, modeled after the
Linux kernel's modular subsystem design. Each tier provides a clear interface
boundary, and lower tiers never depend on upper tiers.

Tier Structure (implemented modules)::

    Tier 0: Base Foundation              → shared/ (schemas, standard_io, config)
    Tier 1: Core Processing (kernel/)    → Classification, NER, Validation, Scoring, etc.
    Tier 2: Cognitive Engines (kernel/)  → Task Decomposition, Curiosity, What-If, Attention

    Tier 3+: Future tiers (orchestration, OODA, lifecycle, observer)

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

Integration Protocol:
    - All functions accept Signal(s) and return Result
    - All errors are KernelError (first-class data, not exceptions)
    - All config flows from shared.config.get_settings().kernel
    - All logging uses shared.logging.main.get_logger(__name__)
    - Tier 2 modules call Tier 1 primitives; never the reverse
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
]
