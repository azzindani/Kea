"""
Tier 6: Noise Gate Module.

Final quality checkpoint: multi-dimensional quality threshold,
output annotation, rejection with retry guidance, and retry budget.

Usage::

    from kernel.noise_gate import filter_output, ToolOutput

    output = ToolOutput(output_id="out_001", content="...")
    result = await filter_output(output, grounding_report, calibrated_conf)
"""

from .engine import (
    annotate_output,
    apply_quality_threshold,
    check_retry_budget,
    clear_retry_budget,
    filter_output,
    generate_rejection_feedback,
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

__all__ = [
    # Engine functions
    "filter_output",
    "apply_quality_threshold",
    "annotate_output",
    "generate_rejection_feedback",
    "check_retry_budget",
    "clear_retry_budget",
    # Types
    "ToolOutput",
    "QualityMetadata",
    "FilteredOutput",
    "RejectedOutput",
    "RejectionDimension",
    "RetryGuidance",
    "RetryBudgetStatus",
]
