"""
Tier 8: Workforce Manager Module.

Pure-logic skill matching, performance evaluation, and scaling decisions
for the Corporation Kernel's agent workforce.

Usage::

    from kernel.workforce_manager import match_specialist, evaluate_performance

    match = match_specialist(chunk, available_profiles)
    snapshot = evaluate_performance(handle, agent_response)
"""

from .engine import (
    compute_scale_decisions,
    evaluate_performance,
    match_specialist,
)
from .types import (
    AgentHandle,
    AgentStatus,
    MissionChunk,
    PerformanceSnapshot,
    ProfileMatch,
    ScaleAction,
    ScaleDecision,
    TerminationReason,
    WorkforcePool,
)

__all__ = [
    # Engine functions
    "match_specialist",
    "evaluate_performance",
    "compute_scale_decisions",
    # Types
    "MissionChunk",
    "AgentHandle",
    "AgentStatus",
    "WorkforcePool",
    "TerminationReason",
    "ScaleDecision",
    "ScaleAction",
    "ProfileMatch",
    "PerformanceSnapshot",
]
