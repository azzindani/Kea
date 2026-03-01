"""
Tier 6: Cognitive Load Monitor Module.

Processing budget measurement and anomaly detection: load measurement,
loop/stall/oscillation/drift detection, and graduated response actions.

Usage::

    from kernel.cognitive_load_monitor import monitor_cognitive_load

    result = await monitor_cognitive_load(
        activation_map, telemetry, recent_decisions,
    )
"""

from .engine import (
    detect_goal_drift,
    detect_loop,
    detect_oscillation,
    detect_stall,
    measure_load,
    monitor_cognitive_load,
    recommend_action,
)
from .types import (
    CognitiveLoad,
    CycleTelemetry,
    GoalDriftDetection,
    LoadAction,
    LoadRecommendation,
    LoopDetection,
    OscillationDetection,
)

__all__ = [
    # Engine functions
    "monitor_cognitive_load",
    "measure_load",
    "detect_loop",
    "detect_stall",
    "detect_oscillation",
    "detect_goal_drift",
    "recommend_action",
    # Types
    "CycleTelemetry",
    "CognitiveLoad",
    "LoopDetection",
    "OscillationDetection",
    "GoalDriftDetection",
    "LoadAction",
    "LoadRecommendation",
]
