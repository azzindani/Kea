"""
Tier 2: Curiosity Engine Module.

Identifies missing knowledge and creates exploration strategies.

Usage::

    from kernel.curiosity_engine import explore_gaps
    from kernel.task_decomposition import WorldState

    state = WorldState(goal="Analyze revenue for Q3")
    result = await explore_gaps(state)
"""

from .engine import (
    detect_missing_variables,
    explore_gaps,
    formulate_questions,
    route_exploration_strategy,
)
from .types import (
    ExplorationQuery,
    ExplorationStrategy,
    ExplorationTask,
    KnowledgeGap,
)

__all__ = [
    "explore_gaps",
    "detect_missing_variables",
    "formulate_questions",
    "route_exploration_strategy",
    "KnowledgeGap",
    "ExplorationQuery",
    "ExplorationStrategy",
    "ExplorationTask",
]
