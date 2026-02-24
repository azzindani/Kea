"""
Tier 6: Confidence Calibrator Module.

Accuracy-confidence alignment: domain-specific calibration curves,
Platt-style correction, overconfidence/underconfidence detection,
and EMA-based feedback learning.

Usage::

    from kernel.confidence_calibrator import run_confidence_calibration

    result = await run_confidence_calibration(
        stated_confidence=0.90, grounding_score=0.75,
        history=calibration_history, domain="finance",
    )
"""

from .engine import (
    calibrate_confidence,
    detect_overconfidence,
    detect_underconfidence,
    get_calibration_curve,
    run_confidence_calibration,
    update_calibration_curve,
)
from .types import CalibratedConfidence

__all__ = [
    # Engine functions
    "run_confidence_calibration",
    "calibrate_confidence",
    "detect_overconfidence",
    "detect_underconfidence",
    "update_calibration_curve",
    "get_calibration_curve",
    # Types
    "CalibratedConfidence",
]
