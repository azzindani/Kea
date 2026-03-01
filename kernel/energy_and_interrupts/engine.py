"""
Tier 5 Energy & Interrupts — Engine.

Resource monitoring and corporate interrupt handling:
    1. Track budget consumption (tokens, cost, compute)
    2. Check budget exhaustion against thresholds
    3. Handle corporate interrupts (kill, override, grant)
    4. Manage lifecycle state transitions
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

from kernel.lifecycle_controller.types import LifecyclePhase
from shared.config import get_settings
from shared.logging.main import get_logger
from shared.standard_io import (
    Metrics,
    ModuleRef,
    Result,
    create_data_signal,
    fail,
    ok,
    processing_error,
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

log = get_logger(__name__)

_MODULE = "energy_and_interrupts"
_TIER = 5


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


def _now_utc() -> str:
    return datetime.now(UTC).isoformat()


# ============================================================================
# Step 1: Track Budget
# ============================================================================


def track_budget(
    cost_event: CostEvent,
    budget_state: BudgetState,
) -> BudgetState:
    """Update the running budget tracker with a new cost event.

    Accumulates consumption across all dimensions and recalculates
    utilization ratio.
    """
    if cost_event.dimension == CostDimension.API_TOKENS:
        budget_state.total_tokens_consumed += int(cost_event.amount)
        budget_state.epoch_tokens_consumed += int(cost_event.amount)
    elif cost_event.dimension == CostDimension.COMPUTE_MS:
        budget_state.total_compute_ms += cost_event.amount
        budget_state.total_cost_consumed += cost_event.amount * 0.00001  # cost per ms
    elif cost_event.dimension == CostDimension.DB_WRITES:
        budget_state.total_db_writes += int(cost_event.amount)
    elif cost_event.dimension == CostDimension.NETWORK_CALLS:
        budget_state.total_network_calls += int(cost_event.amount)

    # Recalculate utilization
    if budget_state.token_limit > 0:
        token_util = budget_state.total_tokens_consumed / budget_state.token_limit
    else:
        token_util = 0.0

    if budget_state.cost_limit > 0:
        cost_util = budget_state.total_cost_consumed / budget_state.cost_limit
    else:
        cost_util = 0.0

    budget_state.utilization = max(token_util, cost_util)

    return budget_state


# ============================================================================
# Step 2: Check Budget Exhaustion
# ============================================================================


def check_budget_exhaustion(budget_state: BudgetState) -> bool:
    """Evaluate whether the agent has exhausted its assigned budget.

    Returns True if any budget dimension exceeds the exhaustion threshold.
    """
    settings = get_settings().kernel
    threshold = settings.budget_exhaustion_threshold

    return budget_state.utilization >= threshold


def check_budget_warning(budget_state: BudgetState) -> bool:
    """Check if budget is approaching exhaustion (warning zone)."""
    settings = get_settings().kernel
    return budget_state.utilization >= settings.budget_warning_threshold


# ============================================================================
# Step 3: Handle Interrupts
# ============================================================================


async def handle_interrupt(
    interrupt_signal: InterruptSignal,
) -> InterruptAction:
    """Process top-down control signals from Corporate Kernel.

    Handles priority overrides, kill signals, budget grants,
    and reconfiguration requests.
    """
    action_map: dict[InterruptType, InterruptAction] = {
        InterruptType.PRIORITY_OVERRIDE: InterruptAction.SWITCH_OBJECTIVE,
        InterruptType.KILL: InterruptAction.TERMINATE,
        InterruptType.BUDGET_GRANT: InterruptAction.RESUME,
        InterruptType.RECONFIGURE: InterruptAction.RELOAD_PROFILE,
    }

    action = action_map.get(interrupt_signal.interrupt_type, InterruptAction.IGNORE)

    log.info(
        "Interrupt handled",
        interrupt_type=interrupt_signal.interrupt_type.value,
        action=action.value,
        reason=interrupt_signal.reason,
    )

    return action


# ============================================================================
# Step 4: Manage Lifecycle State
# ============================================================================


async def manage_lifecycle_state(
    trigger: ControlTrigger,
    current_phase: LifecyclePhase,
    agent_id: str = "",
) -> LifecycleTransition:
    """Execute agent state transitions based on control triggers.

    Coordinates with Tier 4's OODA loop to ensure graceful transitions.
    """
    transition_map: dict[
        tuple[LifecyclePhase, ControlTriggerSource], LifecyclePhase
    ] = {
        (LifecyclePhase.ACTIVE, ControlTriggerSource.BUDGET_EXHAUSTED): LifecyclePhase.SUSPENDED,
        (LifecyclePhase.ACTIVE, ControlTriggerSource.INTERRUPT_RECEIVED): LifecyclePhase.SUSPENDED,
        (LifecyclePhase.ACTIVE, ControlTriggerSource.PANIC_DETECTED): LifecyclePhase.PANICKING,
        (LifecyclePhase.ACTIVE, ControlTriggerSource.OODA_COMPLETE): LifecyclePhase.SLEEPING,
        (LifecyclePhase.SUSPENDED, ControlTriggerSource.NETWORK_RESTORED): LifecyclePhase.ACTIVE,
        (LifecyclePhase.SUSPENDED, ControlTriggerSource.MANUAL_OVERRIDE): LifecyclePhase.ACTIVE,
        (LifecyclePhase.PANICKING, ControlTriggerSource.NETWORK_RESTORED): LifecyclePhase.ACTIVE,
        (LifecyclePhase.SLEEPING, ControlTriggerSource.INTERRUPT_RECEIVED): LifecyclePhase.ACTIVE,
    }

    key = (current_phase, trigger.source)
    new_phase = transition_map.get(key, current_phase)

    transition = LifecycleTransition(
        from_phase=current_phase.value,
        to_phase=new_phase.value,
        trigger=trigger,
        timestamp_utc=_now_utc(),
        agent_id=agent_id,
    )

    log.info(
        "Lifecycle state transition",
        from_phase=current_phase.value,
        to_phase=new_phase.value,
        trigger=trigger.source.value,
    )

    return transition


# ============================================================================
# Top-Level Orchestrator
# ============================================================================


async def enforce_energy_authority(
    cost_events: list[CostEvent],
    interrupt_signals: list[InterruptSignal],
    budget_state: BudgetState,
    current_phase: LifecyclePhase,
    agent_id: str = "",
) -> Result:
    """Top-level resource + interrupt monitor.

    Processes pending cost events and interrupt signals, then decides
    whether the agent can continue, must pause, or must terminate.
    """
    ref = _ref("enforce_energy_authority")
    start = time.perf_counter()

    try:
        # Process cost events
        for event in cost_events:
            budget_state = track_budget(event, budget_state)

        # Check budget status
        is_exhausted = check_budget_exhaustion(budget_state)
        is_warning = check_budget_warning(budget_state)

        if is_warning and not is_exhausted:
            log.warning(
                "Budget approaching exhaustion",
                utilization=round(budget_state.utilization, 3),
            )

        # Process interrupts
        action = ControlAction.CONTINUE
        new_objective: str | None = None
        reasoning = "Normal operation"

        for signal in interrupt_signals:
            interrupt_action = await handle_interrupt(signal)

            if interrupt_action == InterruptAction.TERMINATE:
                action = ControlAction.TERMINATE
                reasoning = f"Kill signal received: {signal.reason}"
                break
            elif interrupt_action == InterruptAction.SWITCH_OBJECTIVE:
                action = ControlAction.SWITCH
                new_objective = signal.payload.get("objective", "")
                reasoning = f"Priority override: {signal.reason}"
                break
            elif interrupt_action == InterruptAction.RESUME:
                # Budget grant — update limits
                if "token_limit" in signal.payload:
                    budget_state.token_limit = signal.payload["token_limit"]
                if "cost_limit" in signal.payload:
                    budget_state.cost_limit = signal.payload["cost_limit"]
                reasoning = "Budget granted, resuming"

        # Budget exhaustion overrides normal operation
        if is_exhausted and action == ControlAction.CONTINUE:
            action = ControlAction.SUSPEND
            reasoning = (
                f"Budget exhausted (utilization: {budget_state.utilization:.1%})"
            )

        decision = ControlDecision(
            action=action,
            reasoning=reasoning,
            budget_state=budget_state,
            new_objective=new_objective,
        )

        # Execute lifecycle transition if needed
        if action != ControlAction.CONTINUE:
            trigger_source = {
                ControlAction.SUSPEND: ControlTriggerSource.BUDGET_EXHAUSTED,
                ControlAction.TERMINATE: ControlTriggerSource.INTERRUPT_RECEIVED,
                ControlAction.SWITCH: ControlTriggerSource.INTERRUPT_RECEIVED,
                ControlAction.PANIC: ControlTriggerSource.PANIC_DETECTED,
            }.get(action, ControlTriggerSource.MANUAL_OVERRIDE)

            await manage_lifecycle_state(
                ControlTrigger(source=trigger_source, description=reasoning),
                current_phase,
                agent_id,
            )

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        signal_out = create_data_signal(
            data=decision.model_dump(),
            schema="ControlDecision",
            origin=ref,
            trace_id="",
            tags={
                "action": action.value,
                "utilization": f"{budget_state.utilization:.3f}",
            },
        )

        log.info(
            "Energy authority decision",
            action=action.value,
            utilization=round(budget_state.utilization, 3),
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal_out], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Energy authority failed: {exc}",
            source=ref,
            detail={"error_type": type(exc).__name__},
        )
        log.error("Energy authority failed", error=str(exc))
        return fail(error=error, metrics=metrics)
