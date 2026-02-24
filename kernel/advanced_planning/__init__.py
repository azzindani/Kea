"""
Tier 3: Advanced Planning Module.

DAG sequencing, tool binding, hypothesis generation, and
progress tracking for OODA loop monitoring.

Usage::

    from kernel.advanced_planning import plan_advanced
    from kernel.task_decomposition.types import SubTaskItem

    subtasks = [SubTaskItem(id="t1", description="Step 1")]
    result = await plan_advanced(subtasks)
"""

from .engine import (
    bind_tools,
    generate_hypotheses,
    inject_progress_tracker,
    plan_advanced,
    sequence_and_prioritize,
)
from .types import (
    BoundTask,
    ExpectedOutcome,
    MCPToolBinding,
    MCPToolRegistry,
    PlanningConstraints,
    PriorityMode,
    ProgressTracker,
    SequencedTask,
    TrackedPlan,
)

__all__ = [
    "plan_advanced",
    "sequence_and_prioritize",
    "bind_tools",
    "generate_hypotheses",
    "inject_progress_tracker",
    "BoundTask",
    "ExpectedOutcome",
    "MCPToolBinding",
    "MCPToolRegistry",
    "PlanningConstraints",
    "PriorityMode",
    "ProgressTracker",
    "SequencedTask",
    "TrackedPlan",
]
