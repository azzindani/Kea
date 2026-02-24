"""
Tier 2: Attention & Plausibility Module.

Two-stage cognitive filtering: attention masking + plausibility/sanity checking.

Usage::

    from kernel.attention_and_plausibility import run_cognitive_filters, TaskState, ContextElement

    state = TaskState(
        goal="Analyze Q3 revenue trends",
        context_elements=[
            ContextElement(key="revenue_data", value="Q3 spreadsheet", source="vault"),
            ContextElement(key="weather", value="sunny", source="api"),
        ],
    )
    result = await run_cognitive_filters(state)
"""

from .engine import (
    check_plausibility,
    filter_attention,
    run_cognitive_filters,
)
from .types import (
    ContextElement,
    FilteredState,
    PlausibilityResult,
    PlausibilityVerdict,
    RefinedState,
    SanityAlert,
    TaskState,
)

__all__ = [
    "run_cognitive_filters",
    "filter_attention",
    "check_plausibility",
    "TaskState",
    "ContextElement",
    "FilteredState",
    "PlausibilityResult",
    "PlausibilityVerdict",
    "RefinedState",
    "SanityAlert",
]
