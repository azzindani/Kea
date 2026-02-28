import pytest

from kernel.ooda_loop.engine import (
    observe,
    orient,
    decide,
    act,
    run_ooda_loop
)
from kernel.ooda_loop.types import AgentState, EventStream, MacroObjective, DecisionAction, LoopTerminationReason
from kernel.short_term_memory.engine import ShortTermMemory
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("objective_text, initial_event", [
    ("Check system status and report back", "System heartbeat detected in sector 7G"),
    ("Identify and fix security vulnerability", "High-severity CVE reported in script_x.py"),
])
async def test_ooda_loop_comprehensive(objective_text, initial_event, inference_kit):
    """REAL SIMULATION: Verify OODA Loop with event stimulus and goal achievement."""
    print(f"\n--- Testing OODA Loop: Objective='{objective_text}' ---")

    from kernel.short_term_memory.engine import ShortTermMemory
    from kernel.short_term_memory.types import ObservationEvent, EventSource
    
    stm = ShortTermMemory()
    obj = MacroObjective(objective_id="obj-001", description=objective_text)
    state = AgentState(agent_id="test_agent", current_objectives=[obj])
    
    # Create an initial stimulus event
    trigger = ObservationEvent(
        event_id="evt-trigger-001",
        source=EventSource.USER if "report" in objective_text else EventSource.SYSTEM,
        description=initial_event,
        payload={"target": "script_x.py"}
    )

    print("\n[Test]: Phase 1 & 2 (Observe & Orient with Stimulus)")
    print(f"   [INPUT]: event='{initial_event}'")
    observations = await observe(EventStream(stream_id="test-val"), stm, pending_events=[trigger])
    assert len(observations) == 1
    
    oriented_state = await orient(observations, stm, kit=inference_kit)
    assert oriented_state.observation_summary != ""
    print(f"   [OUTPUT]: Orientation Summary='{oriented_state.observation_summary[:50]}...'")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: Phase 3 (Decide - Planning Intent)")
    decision = await decide(oriented_state, current_objectives=state.current_objectives)
    assert decision.action == DecisionAction.REPLAN
    print(f"   [OUTPUT]: Decision={decision.action} (Correctly requested planning)")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: Phase 4 (Act - Goal Achievement)")
    # Simulating that we have a DAG and one node completed
    from kernel.graph_synthesizer.types import ExecutableDAG, SubTaskItem
    node = SubTaskItem(id="node-1", description="Verify status")
    dag = ExecutableDAG(dag_id="dag-1", nodes=[node], edges=[], description=objective_text)
    
    # Mark objective as completed to test loop termination
    state.current_objectives[0].completed = True
    
    print(f"   [INPUT]: Stimulating objective completion")
    res = await run_ooda_loop(state, stm=stm, active_dag=dag, kit=inference_kit)
    
    assert res.is_success
    assert res.signals[0].body["data"]["termination_reason"] == LoopTerminationReason.OBJECTIVE_COMPLETE
    print(f"   [OUTPUT]: Status={res.status}, Reason={res.signals[0].body['data']['termination_reason']}")
    print(" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
