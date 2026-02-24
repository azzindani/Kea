"""
Tier 2: Task Decomposition Module.

Breaks high-level goals into actionable sub-tasks with dependency graphs.

Usage::

    from kernel.task_decomposition import decompose_goal, WorldState

    state = WorldState(goal="Build and deploy the reporting dashboard")
    result = await decompose_goal(state)
"""

from .engine import (
    analyze_goal_complexity,
    build_dependency_array,
    decompose_goal,
    map_required_skills,
    split_into_sub_goals,
)
from .types import (
    ComplexityAssessment,
    ComplexityLevel,
    DependencyEdge,
    DependencyGraph,
    SubGoal,
    SubTaskItem,
    WorldState,
)

__all__ = [
    "decompose_goal",
    "analyze_goal_complexity",
    "split_into_sub_goals",
    "build_dependency_array",
    "map_required_skills",
    "WorldState",
    "ComplexityLevel",
    "ComplexityAssessment",
    "SubGoal",
    "DependencyEdge",
    "DependencyGraph",
    "SubTaskItem",
]
