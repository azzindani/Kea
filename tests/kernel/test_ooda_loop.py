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
async def test_ooda_loop_comprehensive(objective_text, inference_kit):
    """REAL SIMULATION: Verify OODA Loop Kernel functions with multiple objectives."""
    print(f"\n--- Testing OODA Loop: Objective='{objective_text}' ---")

    stm = ShortTermMemory()
    obj = MacroObjective(description=objective_text)
    state = AgentState(agent_id="test_agent", current_objectives=[obj])
    stream = EventStream(stream_id="test_stream")

    print("\n[Test]: observe")
    print(f"   [INPUT]: stream_id={stream.stream_id}")
    events = await observe(stream, stm)
    assert isinstance(events, list)
    print(f"   [OUTPUT]: Events observed count={len(events)}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: orient")
    print(f"   [INPUT]: {len(events)} events")
    oriented_state = await orient(events, stm, kit=inference_kit)
    assert oriented_state is not None
    print(f"   [OUTPUT]: Oriented state obtained")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: decide")
    print(f"   [INPUT]: current_objectives={len(state.current_objectives)}")
    decision = await decide(oriented_state, current_objectives=state.current_objectives, stm=stm)
    assert decision is not None
    print(f"   [OUTPUT]: Decision made: {decision.action_type if hasattr(decision, 'action_type') else 'None'}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: act")
    print(f"   [INPUT]: decision_type={decision.action_type if hasattr(decision, 'action_type') else 'None'}")
    action_res = await act(decision, active_dag=None, stm=stm)
    assert isinstance(action_res, list)
    print(f"   [OUTPUT]: Action results count={len(action_res)}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: run_ooda_loop")
    print(f"   [INPUT]: objective='{objective_text}'")
    res = await run_ooda_loop(state, stm=stm, kit=inference_kit)
    assert res.is_success
    print(f"   [OUTPUT]: Status={res.status}, Signals count={len(res.signals)}")
    print(" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
