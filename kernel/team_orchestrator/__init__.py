"""
Tier 8: Team Orchestrator Module.

Pure-logic sprint planning, DAG building, and sprint review
for the Corporation Kernel's team coordination.

Usage::

    from kernel.team_orchestrator import plan_sprints, build_sprint_dag, review_sprint

    sprints = await plan_sprints(chunks, kit)
    dag = build_sprint_dag(sprint)
    review = await review_sprint(sprint, result, kit)
"""

from .engine import (
    build_sprint_dag,
    plan_sprints,
    review_sprint,
)
from .types import (
    CorporateOODAResult,
    MissionResult,
    Sprint,
    SprintResult,
    SprintReview,
)

__all__ = [
    # Engine functions
    "plan_sprints",
    "build_sprint_dag",
    "review_sprint",
    # Types
    "Sprint",
    "SprintResult",
    "SprintReview",
    "MissionResult",
    "CorporateOODAResult",
]
