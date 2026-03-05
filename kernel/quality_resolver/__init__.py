"""
Tier 8: Quality Resolver Module.

Pure-logic conflict detection, resolution, and quality scoring
for the Corporation Kernel's multi-agent output validation.

Usage::

    from kernel.quality_resolver import detect_conflicts, resolve_conflict

    conflicts = await detect_conflicts(artifacts, kit)
    resolution = await resolve_conflict(conflict, artifact_a, artifact_b, kit)
"""

from .engine import (
    detect_conflicts,
    resolve_conflict,
    score_sprint_quality,
)
from .types import (
    Conflict,
    FinalQualityReport,
    QualityAudit,
    Resolution,
)

__all__ = [
    # Engine functions
    "detect_conflicts",
    "resolve_conflict",
    "score_sprint_quality",
    # Types
    "Conflict",
    "Resolution",
    "QualityAudit",
    "FinalQualityReport",
]
