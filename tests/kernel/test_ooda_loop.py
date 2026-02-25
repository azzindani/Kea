import pytest

from kernel.ooda_loop.engine import (
    run_observe_phase,
    run_orient_phase,
    run_decide_phase,
    run_act_phase,
    run_ooda_loop
)
from kernel.short_term_memory.engine import ShortTermMemory
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("objective_text", [
    "Check system status and report back",
    "Identify and fix security vulnerability in script_x.py",
    "Find sales trends for Q3 in the database",
    "Hello",
    ""
])
async def test_ooda_loop_comprehensive(objective_text):
    """REAL SIMULATION: Verify OODA Loop Kernel functions with multiple objectives."""
    print(f"\n--- Testing OODA Loop: Objective='{objective_text}' ---")

    stm = ShortTermMemory()

    print(f"\n[Test]: run_observe_phase")
    observation_res = await run_observe_phase(stm)
    assert observation_res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: run_orient_phase")
    orientation_res = await run_orient_phase(observation_res, stm)
    assert orientation_res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: run_decide_phase")
    decision_res = await run_decide_phase(orientation_res, kit=None)
    assert decision_res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: run_act_phase")
    action_res = await run_act_phase(decision_res, stm)
    assert action_res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: run_ooda_loop")
    res = await run_ooda_loop(objective_text, stm=stm)
    assert res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
