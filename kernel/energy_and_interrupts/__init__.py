"""
Tier 5: Energy & Interrupts Module.

Resource monitoring and corporate interrupt handling: budget tracking,
exhaustion detection, interrupt processing, and lifecycle transitions.

Usage::

    from kernel.energy_and_interrupts import enforce_energy_authority, BudgetState

    budget = BudgetState(token_limit=1_000_000, cost_limit=100.0)
    result = await enforce_energy_authority(
        cost_events=[], interrupt_signals=[], budget_state=budget,
        current_phase=LifecyclePhase.ACTIVE,
    )
"""

from .engine import (
    check_budget_exhaustion,
    check_budget_warning,
    enforce_energy_authority,
    handle_interrupt,
    manage_lifecycle_state,
    track_budget,
)
from .types import (
    BudgetState,
    ControlAction,
    ControlDecision,
    ControlTrigger,
    ControlTriggerSource,
    CostDimension,
    CostEvent,
    InterruptAction,
    InterruptSignal,
    InterruptType,
    LifecycleTransition,
)

__all__ = [
    # Engine functions
    "enforce_energy_authority",
    "track_budget",
    "check_budget_exhaustion",
    "check_budget_warning",
    "handle_interrupt",
    "manage_lifecycle_state",
    # Types
    "CostDimension",
    "CostEvent",
    "BudgetState",
    "InterruptType",
    "InterruptSignal",
    "InterruptAction",
    "ControlTriggerSource",
    "ControlTrigger",
    "LifecycleTransition",
    "ControlAction",
    "ControlDecision",
]
