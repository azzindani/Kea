"""
Cognitive Layer.

Decomposed cognitive cycle phases: Perceive, Frame, Plan, Execute, Monitor, Adapt, Package.
Each phase is a single-responsibility module; `cycle.py` chains them together.
"""

from kernel.cognition.cycle import CognitiveCycle, CycleOutput
from kernel.cognition.base import CycleContext, CyclePhase, BasePhase
from kernel.cognition.perceiver import Perceiver, PerceptionResult
from kernel.cognition.framer import Framer, FramingResult
from kernel.cognition.planner import Planner
from kernel.cognition.executor import Executor
from kernel.cognition.monitor import Monitor, MonitorResult
from kernel.cognition.adapter import Adapter
from kernel.cognition.packager import Packager

__all__ = [
    "CognitiveCycle",
    "CycleOutput",
    "CycleContext",
    "CyclePhase",
    "BasePhase",
    "Perceiver",
    "PerceptionResult",
    "Framer",
    "FramingResult",
    "Planner",
    "Executor",
    "Monitor",
    "MonitorResult",
    "Adapter",
    "Packager",
]
