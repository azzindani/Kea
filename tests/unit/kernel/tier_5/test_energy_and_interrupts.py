import pytest

from kernel.energy_and_interrupts.engine import (
    check_budget_exhaustion,
    handle_interrupt,
    track_budget,
)
from kernel.energy_and_interrupts.types import (
    BudgetState,
    CostDimension,
    CostEvent,
    InterruptAction,
    InterruptSignal,
    InterruptType,
)


def test_track_budget():
    bs = BudgetState(token_limit=100)
    ev = CostEvent(dimension=CostDimension.API_TOKENS, amount=50.0, description="")

    bs = track_budget(ev, bs)
    assert bs.total_tokens_consumed == 50
    assert bs.utilization == 0.5

def test_check_budget_exhaustion(monkeypatch):
    class MockSettings:
        budget_exhaustion_threshold: float = 0.9
        budget_warning_threshold: float = 0.8
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.energy_and_interrupts.engine.get_settings", lambda: MockKernelSettings())

    bs = BudgetState(token_limit=100, utilization=0.95)
    assert check_budget_exhaustion(bs)

@pytest.mark.asyncio
async def test_handle_interrupt():
    sig = InterruptSignal(interrupt_type=InterruptType.KILL, reason="testing")
    action = await handle_interrupt(sig)
    assert action == InterruptAction.TERMINATE
