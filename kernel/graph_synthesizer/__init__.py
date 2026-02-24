"""
Tier 3: Graph Synthesizer Module.

JIT DAG compilation: translates Tier 2 sub-tasks into executable
computational graphs with dependency edges and parallel groups.

Usage::

    from kernel.graph_synthesizer import synthesize_plan
    from kernel.task_decomposition import WorldState

    context = WorldState(goal="Build and deploy the dashboard")
    result = await synthesize_plan("Build dashboard", context)
"""

from .engine import (
    calculate_dependency_edges,
    compile_dag,
    map_subtasks_to_nodes,
    review_dag_with_simulation,
    synthesize_plan,
)
from .types import (
    ActionInstruction,
    DAGState,
    Edge,
    EdgeKind,
    ExecutableDAG,
    ExecutableNode,
    NodeStatus,
)

__all__ = [
    "synthesize_plan",
    "map_subtasks_to_nodes",
    "calculate_dependency_edges",
    "compile_dag",
    "review_dag_with_simulation",
    "ActionInstruction",
    "DAGState",
    "Edge",
    "EdgeKind",
    "ExecutableDAG",
    "ExecutableNode",
    "NodeStatus",
]
