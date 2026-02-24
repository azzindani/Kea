"""
Tier 6 Noise Gate — Engine.

Final quality checkpoint before output leaves the kernel:
    1. Apply multi-dimensional quality threshold check
    2. Annotate passing outputs with quality metadata
    3. Generate rejection feedback with retry guidance
    4. Track retry budget to prevent infinite loops
"""

from __future__ import annotations

import time
from typing import Union

from shared.config import get_settings
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

from kernel.confidence_calibrator.types import CalibratedConfidence
from kernel.hallucination_monitor.types import (
    ClaimGradeLevel,
    GroundingReport,
)

from .types import (
    FilteredOutput,
    QualityMetadata,
    RejectedOutput,
    RejectionDimension,
    RetryBudgetStatus,
    RetryGuidance,
    ToolOutput,
)

log = get_logger(__name__)

_MODULE = "noise_gate"
_TIER = 6


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Internal State: Retry Budget Tracker
# ============================================================================

_retry_counts: dict[str, int] = {}


# ============================================================================
# Step 1: Apply Quality Threshold
# ============================================================================


def apply_quality_threshold(
    grounding_score: float,
    confidence: float,
    quality_bar_override: float | None = None,
) -> bool:
    """Core pass/fail decision.

    Checks:
        1. Grounding score >= grounding threshold
        2. Calibrated confidence >= confidence threshold

    Returns True if all pass, False if any fail.
    Thresholds can be overridden per-task by T5 identity constraints.
    """
    settings = get_settings().kernel

    grounding_threshold = settings.noise_gate_grounding_threshold
    confidence_threshold = settings.noise_gate_confidence_threshold

    # Allow T5 identity constraints to override the grounding threshold
    if quality_bar_override is not None:
        grounding_threshold = quality_bar_override

    passes_grounding = grounding_score >= grounding_threshold
    passes_confidence = confidence >= confidence_threshold

    return passes_grounding and passes_confidence


# ============================================================================
# Step 2: Annotate Output
# ============================================================================


def annotate_output(
    output: ToolOutput,
    grounding: GroundingReport,
    confidence: CalibratedConfidence,
) -> FilteredOutput:
    """Enrich a passing output with quality metadata.

    Adds per-claim grounding grades, overall score, calibrated
    confidence, overconfidence warning, and source references.
    """
    # Collect source references from grounded claims
    source_references: list[str] = []
    fabricated_count = 0
    for grade in grounding.claim_grades:
        if grade.grade == ClaimGradeLevel.GROUNDED:
            for link in grade.evidence_links:
                if link.origin_id not in source_references:
                    source_references.append(link.origin_id)
        elif grade.grade == ClaimGradeLevel.FABRICATED:
            fabricated_count += 1

    quality = QualityMetadata(
        grounding_score=grounding.grounding_score,
        calibrated_confidence=confidence.calibrated_confidence,
        overconfidence_warning=confidence.is_overconfident,
        fabricated_claim_count=fabricated_count,
        source_references=source_references,
    )

    return FilteredOutput(
        output_id=output.output_id,
        content=output.content,
        metadata=output.metadata,
        quality=quality,
        passed=True,
    )


# ============================================================================
# Step 3: Generate Rejection Feedback
# ============================================================================


def generate_rejection_feedback(
    output: ToolOutput,
    grounding: GroundingReport,
    confidence: CalibratedConfidence,
) -> RejectedOutput:
    """Generate actionable feedback when an output fails the gate.

    Identifies which dimensions failed, specific fabricated claims,
    and suggestions for improvement.
    """
    settings = get_settings().kernel
    grounding_threshold = settings.noise_gate_grounding_threshold
    confidence_threshold = settings.noise_gate_confidence_threshold

    failed_dimensions: list[RejectionDimension] = []
    suggestions: list[str] = []
    fabricated_claims: list[str] = []

    # Check grounding dimension
    if grounding.grounding_score < grounding_threshold:
        failed_dimensions.append(RejectionDimension.GROUNDING)
        suggestions.append(
            f"Improve grounding: score {grounding.grounding_score:.2f} "
            f"below threshold {grounding_threshold:.2f}"
        )

        # Identify specific fabricated claims
        for grade in grounding.claim_grades:
            if grade.grade == ClaimGradeLevel.FABRICATED:
                fabricated_claims.append(grade.claim_id)

        if fabricated_claims:
            suggestions.append(
                f"Search for evidence to support {len(fabricated_claims)} "
                f"ungrounded claims before restating"
            )

    # Check confidence dimension
    if confidence.calibrated_confidence < confidence_threshold:
        failed_dimensions.append(RejectionDimension.CONFIDENCE)
        suggestions.append(
            f"Confidence too low: {confidence.calibrated_confidence:.2f} "
            f"below threshold {confidence_threshold:.2f}"
        )
        if confidence.is_overconfident:
            suggestions.append("Reduce stated confidence to match evidence quality")

    # Multiple dimensions failed
    if len(failed_dimensions) > 1:
        failed_dimensions = [RejectionDimension.MULTIPLE] + failed_dimensions

    # Get retry budget
    retry_status = check_retry_budget(output.output_id)

    # Build rejection reason
    dim_names = [d.value for d in failed_dimensions if d != RejectionDimension.MULTIPLE]
    rejection_reason = f"Failed quality gate on: {', '.join(dim_names)}"

    guidance = RetryGuidance(
        rejection_reason=rejection_reason,
        failed_dimensions=failed_dimensions,
        fabricated_claims=fabricated_claims,
        suggestions=suggestions,
        retry_count=retry_status.retries_used,
        should_escalate=retry_status.should_escalate,
    )

    if retry_status.should_escalate:
        suggestions.append(
            "Retry budget exhausted — escalate to T5/T7 for human intervention"
        )

    return RejectedOutput(
        output_id=output.output_id,
        content=output.content,
        guidance=guidance,
        passed=False,
    )


# ============================================================================
# Step 4: Check Retry Budget
# ============================================================================


def check_retry_budget(output_id: str) -> RetryBudgetStatus:
    """Check how many retry attempts have been made for this output.

    Increments the counter and returns the current status.
    """
    settings = get_settings().kernel
    max_retries = settings.noise_gate_max_retries

    current = _retry_counts.get(output_id, 0)
    current += 1
    _retry_counts[output_id] = current

    remaining = max(0, max_retries - current)
    should_escalate = remaining <= 0

    return RetryBudgetStatus(
        output_id=output_id,
        retries_used=current,
        retries_remaining=remaining,
        should_escalate=should_escalate,
    )


def clear_retry_budget(output_id: str) -> None:
    """Clear the retry counter for a completed output."""
    _retry_counts.pop(output_id, None)


# ============================================================================
# Top-Level Orchestrator
# ============================================================================


async def filter_output(
    output: ToolOutput,
    grounding: GroundingReport,
    confidence: CalibratedConfidence,
    quality_bar_override: float | None = None,
) -> Result:
    """Top-level noise gate filter.

    Applies quality threshold check. If the output passes, annotates
    it with quality metadata. If it fails, generates retry guidance.
    Returns a standard Result containing either a FilteredOutput or
    RejectedOutput.
    """
    ref = _ref("filter_output")
    start = time.perf_counter()

    try:
        passes = apply_quality_threshold(
            grounding.grounding_score,
            confidence.calibrated_confidence,
            quality_bar_override,
        )

        result_data: Union[FilteredOutput, RejectedOutput]

        if passes:
            result_data = annotate_output(output, grounding, confidence)
            schema_name = "FilteredOutput"

            # Clear retry budget on success
            clear_retry_budget(output.output_id)

            log.info(
                "Output passed noise gate",
                output_id=output.output_id,
                grounding_score=round(grounding.grounding_score, 3),
                confidence=round(confidence.calibrated_confidence, 3),
            )
        else:
            result_data = generate_rejection_feedback(
                output, grounding, confidence,
            )
            schema_name = "RejectedOutput"

            log.warning(
                "Output rejected by noise gate",
                output_id=output.output_id,
                grounding_score=round(grounding.grounding_score, 3),
                confidence=round(confidence.calibrated_confidence, 3),
                should_escalate=result_data.guidance.should_escalate,
            )

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        signal = create_data_signal(
            data=result_data.model_dump(),
            schema=schema_name,
            origin=ref,
            trace_id="",
            tags={
                "passed": str(result_data.passed),
                "output_id": output.output_id,
                "grounding_score": f"{grounding.grounding_score:.3f}",
                "confidence": f"{confidence.calibrated_confidence:.3f}",
            },
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Noise gate filtering failed: {exc}",
            source=ref,
            detail={"output_id": output.output_id, "error_type": type(exc).__name__},
        )
        log.error("Noise gate filtering failed", error=str(exc))
        return fail(error=error, metrics=metrics)
