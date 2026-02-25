import pytest

from kernel.ooda_loop.engine import (
    observe,
    orient,
    decide,
    act,
    run_ooda_loop
)
from kernel.ooda_loop.types import AgentState, EventStream, MacroObjective
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
    obj = MacroObjective(description=objective_text)
    state = AgentState(agent_id="test_agent", current_objectives=[obj])
    stream = EventStream(stream_id="test_stream")

    print("\n[Test]: observe")
    events = await observe(stream, stm)
    assert isinstance(events, list)
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: orient")
    oriented_state = await orient(events, stm, kit=None)
    assert oriented_state is not None
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: decide")
    decision = await decide(oriented_state, current_objectives=state.current_objectives, stm=stm)
    assert decision is not None
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: act")
    action_res = await act(decision, active_dag=None, stm=stm)
    assert isinstance(action_res, list)
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: run_ooda_loop")
    res = await run_ooda_loop(state, stm=stm, kit=None)
    assert res.is_success
    print(" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
