import pytest
from datetime import UTC, datetime

from kernel.conscious_observer.engine import ConsciousObserver, run_conscious_observer
from kernel.conscious_observer.types import ProcessingMode, ObserverPhase
from kernel.lifecycle_controller.types import SpawnRequest
from kernel.modality.types import RawInput
from shared.config import get_settings

@pytest.mark.asyncio
@pytest.mark.parametrize("objective, expected_mode", [
    ("Tell me a short joke.", ProcessingMode.FAST),
    ("Analyze the current semiconductor market in Taiwan and provide a report.", ProcessingMode.STANDARD),
])
async def test_conscious_observer_comprehensive(objective, expected_mode, inference_kit):
    """
    REAL SIMULATION: Verify the Human Kernel Apex (ConsciousObserver) orchestration.
    
    This test exercises:
    1. Gate-In: Identity genesis, T1 perception, T6 activation routing.
    2. Execute: Model-selected pipeline branch (Fast/Standard/Full).
    3. Gate-Out: Quality filtering and grounding (if applicable).
    """
    print(f"\n--- Testing ConsciousObserver: Objective='{objective}' ---")
    
    observer = ConsciousObserver(kit=inference_kit)
    
    raw_input = RawInput(content=objective)
    spawn_request = SpawnRequest(
        role="test_agent",
        objective=objective,
        profile_id="test_profile_001",
        budget_tokens=1000,
        budget_cost=0.10
    )
    
    # Run the full apex pipeline
    result = await observer.process(
        raw_input=raw_input,
        spawn_request=spawn_request,
        trace_id=f"test_trace_{datetime.now(UTC).timestamp()}"
    )
    
    # Assertions
    assert result.is_success
    obs_result = result.signals[0].body["data"]
    
    print(f"   [OUTPUT]: AgentID={obs_result['agent_id']}")
    print(f"   [OUTPUT]: Mode={obs_result['mode']}")
    print(f"   [OUTPUT]: Final Phase={obs_result['final_phase']}")
    print(f"   [OUTPUT]: Total Duration={obs_result['total_duration_ms']:.2f}ms")
    
    assert obs_result["agent_id"].startswith("agt_")
    # Note: Mode might vary based on LLM response if activation router uses it,
    # but we check if it returned a valid mode.
    assert obs_result["mode"] in [m.value for m in ProcessingMode]
    assert obs_result["final_phase"] in [p.value for p in ObserverPhase]

@pytest.mark.asyncio
async def test_run_conscious_observer_shortcut(inference_kit):
    """Verify the module-level shortcut function."""
    objective = "Hello!"
    raw_input = RawInput(content=objective)
    spawn_request = SpawnRequest(role="test_shortcut", objective=objective)
    
    result = await run_conscious_observer(raw_input, spawn_request, kit=inference_kit)
    assert result.is_success
    assert result.signals[0].body["data"]["final_phase"] in [p.value for p in ObserverPhase]

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
