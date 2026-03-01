"""
Tier 6 Confidence Calibrator — Engine.

Accuracy-confidence alignment:
    1. Calibrate stated confidence using domain-specific curves
    2. Detect overconfidence (stated >> calibrated)
    3. Detect underconfidence (calibrated >> stated)
    4. Update calibration curve via feedback learning (EMA)
    5. Retrieve domain-specific calibration curves
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

from kernel.self_model.engine import update_accuracy_history
from kernel.self_model.types import (
    CalibrationCurve,
    CalibrationHistory,
)
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

from .types import CalibratedConfidence

log = get_logger(__name__)

_MODULE = "confidence_calibrator"
_TIER = 6


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Internal State: Domain-Specific Calibration Curves
# ============================================================================

_domain_curves: dict[str, CalibrationCurve] = {}


# ============================================================================
# Step 1: Calibrate Confidence
# ============================================================================


def calibrate_confidence(
    stated_confidence: float,
    grounding_score: float,
    history: CalibrationHistory,
    domain: str = "general",
) -> CalibratedConfidence:
    """Top-level calibration.

    Looks up the domain-specific calibration curve, applies the
    correction factor, integrates grounding score as a hard upper
    bound, and returns the calibrated result.

    Formula: calibrated = min(historical_correction(stated), grounding_score)
    """
    # Get calibration curve for this domain
    curve = get_calibration_curve(domain)

    # Apply Platt-style correction from the curve
    # Find the bin that contains the stated confidence
    corrected = _apply_curve_correction(stated_confidence, curve)

    # Grounding score acts as a hard upper bound
    calibrated = min(corrected, grounding_score)

    # Ensure bounds
    calibrated = max(0.0, min(1.0, calibrated))

    # Calculate correction factor
    correction_factor = calibrated / stated_confidence if stated_confidence > 0 else 1.0

    # Detect miscalibration
    is_overconfident = detect_overconfidence(stated_confidence, calibrated)
    is_underconfident = detect_underconfidence(stated_confidence, calibrated)

    # Generate warning message
    warning = ""
    if is_overconfident:
        gap = stated_confidence - calibrated
        warning = (
            f"Overconfidence detected: stated {stated_confidence:.0%} "
            f"but calibrated to {calibrated:.0%} (gap: {gap:.0%})"
        )
    elif is_underconfident:
        gap = calibrated - stated_confidence
        warning = (
            f"Underconfidence detected: stated {stated_confidence:.0%} "
            f"but calibrated to {calibrated:.0%} (gap: {gap:.0%})"
        )

    return CalibratedConfidence(
        stated_confidence=round(stated_confidence, 4),
        calibrated_confidence=round(calibrated, 4),
        correction_factor=round(correction_factor, 4),
        is_overconfident=is_overconfident,
        is_underconfident=is_underconfident,
        domain=domain,
        warning=warning,
    )


def _apply_curve_correction(
    stated: float,
    curve: CalibrationCurve,
) -> float:
    """Apply the calibration curve correction factor.

    Finds the nearest bin in the curve and interpolates.
    """
    if not curve.bin_mapping:
        return stated

    # Convert bin keys to floats and sort
    bins_sorted = sorted(
        [(float(k), v) for k, v in curve.bin_mapping.items()],
        key=lambda x: x[0],
    )

    # Find the two bins that bracket the stated confidence
    lower_bin = bins_sorted[0]
    upper_bin = bins_sorted[-1]

    for i in range(len(bins_sorted) - 1):
        if bins_sorted[i][0] <= stated <= bins_sorted[i + 1][0]:
            lower_bin = bins_sorted[i]
            upper_bin = bins_sorted[i + 1]
            break

    # Linear interpolation
    if upper_bin[0] == lower_bin[0]:
        return lower_bin[1]

    t = (stated - lower_bin[0]) / (upper_bin[0] - lower_bin[0])
    return lower_bin[1] + t * (upper_bin[1] - lower_bin[1])


# ============================================================================
# Step 2: Detect Overconfidence
# ============================================================================


def detect_overconfidence(stated: float, calibrated: float) -> bool:
    """Check if stated confidence significantly exceeds calibrated.

    Returns True if the gap exceeds the configured threshold.
    """
    settings = get_settings().kernel
    threshold = settings.calibration_overconfidence_threshold
    return (stated - calibrated) > threshold


# ============================================================================
# Step 3: Detect Underconfidence
# ============================================================================


def detect_underconfidence(stated: float, calibrated: float) -> bool:
    """Check if calibrated confidence significantly exceeds stated.

    Returns True if the agent is systematically underconfident.
    """
    settings = get_settings().kernel
    threshold = settings.calibration_underconfidence_threshold
    return (calibrated - stated) > threshold


# ============================================================================
# Step 4: Update Calibration Curve (Feedback Loop)
# ============================================================================


def update_calibration_curve(
    predicted: float,
    actual_accuracy: float,
    domain: str = "general",
) -> None:
    """Update the calibration curve for the given domain.

    Uses exponential moving average (EMA) to weight recent data
    points more heavily. Also updates the Self-Model accuracy history.
    """
    settings = get_settings().kernel
    decay = settings.self_model_calibration_ema_decay

    curve = get_calibration_curve(domain)

    # Find the bin key for this prediction
    bin_key = f"{round(predicted, 1):.1f}"

    # Apply EMA update
    if bin_key in curve.bin_mapping:
        current = curve.bin_mapping[bin_key]
        updated = (1 - decay) * current + decay * actual_accuracy
    else:
        updated = actual_accuracy

    curve.bin_mapping[bin_key] = round(updated, 6)
    curve.sample_count += 1
    curve.last_updated_utc = datetime.now(UTC).isoformat()

    # Update the stored curve
    _domain_curves[domain] = curve

    # Propagate to Self-Model accuracy tracker
    update_accuracy_history(predicted, actual_accuracy, domain)

    log.debug(
        "Calibration curve updated",
        domain=domain,
        bin=bin_key,
        predicted=round(predicted, 3),
        actual=round(actual_accuracy, 3),
        sample_count=curve.sample_count,
    )


# ============================================================================
# Step 5: Get Calibration Curve
# ============================================================================


def get_calibration_curve(domain: str = "general") -> CalibrationCurve:
    """Retrieve the calibration curve for a specific domain.

    If no domain-specific curve exists, returns the global default.
    """
    if domain in _domain_curves:
        return _domain_curves[domain].model_copy(deep=True)

    # Build default curve from config
    settings = get_settings().kernel
    default_curve = CalibrationCurve(
        domain=domain,
        bin_mapping=dict(settings.calibration_default_curve),
        sample_count=0,
        last_updated_utc=datetime.now(UTC).isoformat(),
    )

    # Cache it for future use
    _domain_curves[domain] = default_curve

    return default_curve.model_copy(deep=True)


# ============================================================================
# Top-Level Orchestrator
# ============================================================================


async def run_confidence_calibration(
    stated_confidence: float,
    grounding_score: float,
    history: CalibrationHistory,
    domain: str = "general",
) -> Result:
    """Top-level confidence calibration.

    Calibrates the stated confidence, detects miscalibration,
    and returns a CalibratedConfidence via the standard Result.
    """
    ref = _ref("run_confidence_calibration")
    start = time.perf_counter()

    try:
        calibrated = calibrate_confidence(
            stated_confidence, grounding_score, history, domain,
        )

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        signal = create_data_signal(
            data=calibrated.model_dump(),
            schema="CalibratedConfidence",
            origin=ref,
            trace_id="",
            tags={
                "stated": f"{calibrated.stated_confidence:.3f}",
                "calibrated": f"{calibrated.calibrated_confidence:.3f}",
                "overconfident": str(calibrated.is_overconfident),
                "underconfident": str(calibrated.is_underconfident),
                "domain": domain,
            },
        )

        log.info(
            "Confidence calibrated",
            stated=round(stated_confidence, 3),
            calibrated=round(calibrated.calibrated_confidence, 3),
            correction=round(calibrated.correction_factor, 3),
            overconfident=calibrated.is_overconfident,
            domain=domain,
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Confidence calibration failed: {exc}",
            source=ref,
            detail={"error_type": type(exc).__name__},
        )
        log.error("Confidence calibration failed", error=str(exc))
        return fail(error=error, metrics=metrics)
