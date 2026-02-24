"""
Tier 6: Activation Router Module.

Selective module activation for energy conservation: complexity
classification, pipeline selection, pressure adaptation, and caching.

Usage::

    from kernel.activation_router import compute_activation_map, SignalTags

    tags = SignalTags(urgency="high", complexity="complex")
    result = await compute_activation_map(tags, capability, pressure=0.3)
"""

from .engine import (
    cache_decision,
    check_decision_cache,
    classify_signal_complexity,
    compute_activation_map,
    select_pipeline,
)
from .types import (
    ActivationMap,
    ComplexityLevel,
    ModuleActivation,
    PipelineConfig,
)

__all__ = [
    # Engine functions
    "compute_activation_map",
    "classify_signal_complexity",
    "select_pipeline",
    "check_decision_cache",
    "cache_decision",
    # Types
    "ComplexityLevel",
    "ModuleActivation",
    "PipelineConfig",
    "ActivationMap",
]
