"""
Tier 7 Conscious Observer — Human Kernel Apex.

The sole top-level entry point for the Kea Human Kernel. Orchestrates
the full Tier 1–6 cognitive pyramid from raw sensory input to
quality-gated output across three phases:

    Phase 1  GATE-IN   T5 genesis + T1 perception + T6 routing
    Phase 2  EXECUTE   T2/T3/T4 pipeline (mode-selected) + T6 CLM per cycle
    Phase 3  GATE-OUT  T6 grounding → confidence → noise gate → retry

Public API::

    from kernel.conscious_observer import ConsciousObserver, run_conscious_observer

    result = await run_conscious_observer(raw_input, spawn_request, kit=kit)
"""

from __future__ import annotations

from kernel.conscious_observer.engine import (
    ConsciousObserver,
    run_conscious_observer,
)
from kernel.conscious_observer.types import (
    ConsciousObserverResult,
    GateInResult,
    ObserverExecuteResult,
    ObserverPhase,
    ProcessingMode,
)

__all__ = [
    # Class
    "ConsciousObserver",
    # Module-level entry point
    "run_conscious_observer",
    # Result types
    "ConsciousObserverResult",
    "GateInResult",
    "ObserverExecuteResult",
    # Enums
    "ObserverPhase",
    "ProcessingMode",
]
