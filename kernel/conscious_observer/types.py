"""
Tier 7 Conscious Observer — Types.

Data contracts for the Human Kernel Apex orchestrator.
All domain types (ActivationMap, LoopResult, etc.) are imported
from production kernel submodules; only orchestrator-boundary
types are defined here.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from kernel.activation_router.types import ActivationMap
from kernel.classification.types import ClassificationResult, FallbackTrigger
from kernel.confidence_calibrator.types import CalibratedConfidence
from kernel.entity_recognition.types import ValidatedEntity
from kernel.hallucination_monitor.types import GroundingReport, Origin
from kernel.intent_sentiment_urgency.types import CognitiveLabels
from kernel.lifecycle_controller.types import IdentityContext
from kernel.modality.types import ModalityOutput
from kernel.noise_gate.types import FilteredOutput, RejectedOutput, RetryGuidance
from kernel.ooda_loop.types import Decision, LoopResult
from kernel.self_model.types import CapabilityAssessment, SignalTags

# Re-export Origin so callers can import it from this module
__all__ = [
    "ProcessingMode",
    "ObserverPhase",
    "GateInResult",
    "ObserverExecuteResult",
    "ConsciousObserverResult",
    "Origin",
]


# ============================================================================
# Pipeline Mode — Determined by Activation Router Complexity
# ============================================================================


class ProcessingMode(StrEnum):
    """Cognitive pipeline selected by the Activation Router.

    Directly maps from ComplexityLevel to the set of tiers engaged:
        FAST      → TRIVIAL/SIMPLE  → T1 + T4
        STANDARD  → MODERATE        → T1 + T2 + T4
        FULL      → COMPLEX         → T1 + T2 + T3 + T4
        EMERGENCY → CRITICAL        → T1 + T4 (capped cycles) + T5 protocol
    """

    FAST = "fast"
    STANDARD = "standard"
    FULL = "full"
    EMERGENCY = "emergency"


# ============================================================================
# Observer Phase — Last Completed Phase
# ============================================================================


class ObserverPhase(StrEnum):
    """Which phase of the ConsciousObserver pipeline last completed.

    Used in ConsciousObserverResult to surface where processing stopped
    and why, enabling transparent audit trails.
    """

    GATE_IN = "gate_in"
    EXECUTE = "execute"
    GATE_OUT = "gate_out"
    ESCALATED = "escalated"   # Capability gap or CLM ESCALATE signal
    ABORTED = "aborted"       # CLM ABORT signal


# ============================================================================
# Phase 1 Artifact — Gate-In
# ============================================================================


class GateInResult(BaseModel):
    """Artifact bundle produced by Phase 1 (Gate-In).

    Carries the fully initialized agent identity and all Tier 1
    perception outputs alongside the Tier 6 routing decision.
    Passed unchanged into Phase 2 and Phase 3.
    """

    identity_context: IdentityContext
    signal_tags: SignalTags
    modality_output: ModalityOutput
    classification: ClassificationResult | FallbackTrigger
    cognitive_labels: CognitiveLabels
    entities: list[ValidatedEntity] = Field(default_factory=list)
    activation_map: ActivationMap
    capability: CapabilityAssessment
    mode: ProcessingMode
    gate_in_duration_ms: float = Field(default=0.0, ge=0.0)


# ============================================================================
# Phase 2 Artifact — Execute
# ============================================================================


class ObserverExecuteResult(BaseModel):
    """Artifact bundle produced by Phase 2 (Execute).

    Captures the loop result, per-cycle history needed for Gate-Out
    grounding, and CLM adaptation flags.
    """

    loop_result: LoopResult
    raw_artifact: str = Field(
        default="",
        description="Human-readable synthesis of loop artifacts for Gate-Out grounding",
    )
    recent_decisions: list[Decision] = Field(default_factory=list)
    recent_outputs: list[str] = Field(default_factory=list)
    objective: str = Field(default="")
    total_cycles: int = Field(default=0, ge=0)
    was_simplified: bool = Field(
        default=False,
        description="CLM triggered at least one pipeline downgrade",
    )
    was_escalated: bool = Field(
        default=False,
        description="CLM triggered ESCALATE — loop broken early",
    )
    was_aborted: bool = Field(
        default=False,
        description="CLM triggered ABORT — loop terminated immediately",
    )
    execute_duration_ms: float = Field(default=0.0, ge=0.0)


# ============================================================================
# Final Result — ConsciousObserverResult
# ============================================================================


class ConsciousObserverResult(BaseModel):
    """Complete result from a single ConsciousObserver.process() invocation.

    Carries the quality-gated output (success path), or structured
    escalation guidance (rejection path), plus a full audit trail
    for Vault persistence and epoch commit.
    """

    trace_id: str
    agent_id: str
    mode: ProcessingMode
    final_phase: ObserverPhase

    # Success path — Gate-Out passed
    filtered_output: FilteredOutput | None = Field(
        default=None,
        description="Quality-verified output; present only when noise gate passed",
    )

    # Escalation / rejection path
    partial_output: str | None = Field(
        default=None,
        description="Best-effort partial output when gate-out budget is exhausted",
    )
    escalation_guidance: RetryGuidance | None = Field(
        default=None,
        description="Retry guidance from noise gate or CLM escalation",
    )

    # Audit trail (always populated for Vault persistence)
    grounding_report: GroundingReport | None = Field(
        default=None,
        description="Per-claim epistemic grounding grades",
    )
    calibrated_confidence: CalibratedConfidence | None = Field(
        default=None,
        description="Accuracy-aligned confidence estimate",
    )

    # Telemetry
    total_duration_ms: float = Field(default=0.0, ge=0.0)
    total_cycles: int = Field(default=0, ge=0)
    gate_in_ms: float = Field(default=0.0, ge=0.0)
    execute_ms: float = Field(default=0.0, ge=0.0)
    gate_out_ms: float = Field(default=0.0, ge=0.0)

    # Adaptation flags
    was_simplified: bool = False
    was_escalated: bool = False
    was_aborted: bool = False
