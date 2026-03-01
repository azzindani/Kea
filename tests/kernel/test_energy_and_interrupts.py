import pytest

from kernel.energy_and_interrupts.engine import (
    track_budget,
    check_budget_exhaustion,
    check_budget_warning,
    handle_interrupt,
    manage_lifecycle_state,
    enforce_energy_authority
)
from kernel.energy_and_interrupts.types import (
    CostEvent, CostDimension, BudgetState, InterruptSignal, InterruptType,
    ControlTrigger, ControlTriggerSource
)
from kernel.lifecycle_controller.types import LifecyclePhase
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("cost_events, interrupt_signals, initial_budget", [
    # Scenario 1: Low consumption, no interrupts
    (
        [CostEvent(dimension=CostDimension.API_TOKENS, amount=100.0)],
        [],
        BudgetState(token_limit=1000, cost_limit=10.0)
    ),
    # Scenario 2: High consumption (Approaching warning)
    (
        [CostEvent(dimension=CostDimension.API_TOKENS, amount=850.0)],
        [],
        BudgetState(token_limit=1000, cost_limit=10.0)
    ),
    # Scenario 3: Kill signal received
    (
        [],
        [InterruptSignal(interrupt_type=InterruptType.KILL, reason="Emergency Shutdown")],
        BudgetState(token_limit=1000, cost_limit=10.0)
    ),
    # Scenario 4: Priority override
    (
        [],
        [InterruptSignal(interrupt_type=InterruptType.PRIORITY_OVERRIDE, reason="Executive Mandate", payload={"objective": "New urgent goal"})],
        BudgetState(token_limit=1000, cost_limit=10.0)
    )
])
async def test_energy_and_interrupts_comprehensive(cost_events, interrupt_signals, initial_budget):
    """REAL SIMULATION: Verify Energy & Interrupts Kernel functions with multiple inputs."""
    print(f"\n--- Testing Energy & Interrupts: Events={len(cost_events)}, Interrupts={len(interrupt_signals)} ---")

    budget_state = initial_budget

    print(f"\n[Test]: track_budget")
    for event in cost_events:
        print(f"   [INPUT]: event_dimension='{event.dimension.value}', amount={event.amount}")
        budget_state = track_budget(event, budget_state)
    assert budget_state is not None
    print(f"   [OUTPUT]: Current Utilization={budget_state.utilization:.2%}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: check_budget_warning")
    print(f"   [INPUT]: utilization={budget_state.utilization:.2%}")
    warning = check_budget_warning(budget_state)
    print(f"   [OUTPUT]: Budget Warning={warning}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: check_budget_exhaustion")
    print(f"   [INPUT]: utilization={budget_state.utilization:.2%}")
    exhaustion = check_budget_exhaustion(budget_state)
    print(f"   [OUTPUT]: Budget Exhausted={exhaustion}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: handle_interrupt")
    for signal in interrupt_signals:
        print(f"   [INPUT]: interrupt_type='{signal.interrupt_type.value}', reason='{signal.reason}'")
        action = await handle_interrupt(signal)
        assert action is not None
        print(f"   [OUTPUT]: Action={action.value}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: manage_lifecycle_state")
    trigger_source = ControlTriggerSource.INTERRUPT_RECEIVED if interrupt_signals else ControlTriggerSource.OODA_COMPLETE
    trigger = ControlTrigger(source=trigger_source, description="Test transition")
    print(f"   [INPUT]: trigger_source='{trigger.source.value}', current_phase={LifecyclePhase.ACTIVE}")
    transition = await manage_lifecycle_state(trigger, LifecyclePhase.ACTIVE)
    assert transition is not None
    print(f"   [OUTPUT]: Transition={transition.from_phase} -> {transition.to_phase}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: enforce_energy_authority")
    print(f"   [INPUT]: events_count={len(cost_events)}, interrupts_count={len(interrupt_signals)}")
    res = await enforce_energy_authority(cost_events, interrupt_signals, initial_budget, LifecyclePhase.ACTIVE)
    assert res.is_success
    print(f"   [OUTPUT]: Status={res.status}, Signals count={len(res.signals)}")
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
