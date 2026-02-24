"""
Tier 6: Self Model Module.

The agent's internal representation of itself: capability maps,
cognitive state tracking, accuracy history, and gap detection.

Usage::

    from kernel.self_model import run_self_model, SignalTags

    tags = SignalTags(domain="finance", urgency="high")
    result = await run_self_model(tags, identity_context)
"""

from .engine import (
    assess_capability,
    detect_capability_gap,
    get_calibration_history,
    get_current_state,
    refresh_capability_map,
    run_self_model,
    update_accuracy_history,
    update_cognitive_state,
)
from .types import (
    AgentCognitiveState,
    CalibrationCurve,
    CalibrationDataPoint,
    CalibrationHistory,
    CapabilityAssessment,
    CapabilityGap,
    ProcessingPhase,
    SignalTags,
)

__all__ = [
    # Engine functions
    "run_self_model",
    "assess_capability",
    "get_current_state",
    "update_cognitive_state",
    "update_accuracy_history",
    "get_calibration_history",
    "detect_capability_gap",
    "refresh_capability_map",
    # Types
    "SignalTags",
    "CapabilityGap",
    "CapabilityAssessment",
    "ProcessingPhase",
    "AgentCognitiveState",
    "CalibrationDataPoint",
    "CalibrationHistory",
    "CalibrationCurve",
]
