"""
Tier 4: OODA Loop Module.

The real-time execution engine: Observe-Orient-Decide-Act cycles
that bridge internal cognition with the external world.

Usage::

    from kernel.ooda_loop import run_ooda_loop, AgentState

    state = AgentState(agent_id="agent_001")
    result = await run_ooda_loop(state)
"""

from .engine import (
    act,
    decide,
    observe,
    orient,
    run_ooda_cycle,
    run_ooda_loop,
)
from .types import (
    ActionResult,
    AgentState,
    AgentStatus,
    CycleAction,
    CycleResult,
    Decision,
    DecisionAction,
    EventStream,
    LoopResult,
    LoopTerminationReason,
    MacroObjective,
    OrientedState,
)

__all__ = [
    "run_ooda_loop",
    "run_ooda_cycle",
    "observe",
    "orient",
    "decide",
    "act",
    "ActionResult",
    "AgentState",
    "AgentStatus",
    "CycleAction",
    "CycleResult",
    "Decision",
    "DecisionAction",
    "EventStream",
    "LoopResult",
    "LoopTerminationReason",
    "MacroObjective",
    "OrientedState",
]
