"""
⚠️  DEPRECATED — kernel/nodes/

This package is superseded by `kernel/cognition/` as part of the v3.0 redesign
(Phase 6: Graph Refactoring).

The monolithic node functions (keeper.py, planner.py, synthesizer.py) have been
decomposed into single-responsibility cognition phases:

    nodes/keeper.py      → cognition/monitor.py + cognition/adapter.py
    nodes/planner.py     → cognition/planner.py
    nodes/synthesizer.py → cognition/packager.py

The LangGraph state machine in flow/graph.py now delegates to:
    - cognition/swarm_executor.py  (researcher_node)
    - cognition/cycle.py           (solo execution)

DO NOT add new logic here. This directory will be removed in v3.1.
"""

import warnings

warnings.warn(
    "kernel.nodes is deprecated. Use kernel.cognition instead.",
    DeprecationWarning,
    stacklevel=2,
)
