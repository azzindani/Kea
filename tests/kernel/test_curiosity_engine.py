import pytest

from kernel.curiosity_engine.engine import (
    detect_missing_variables,
    formulate_questions,
    route_exploration_strategy,
    explore_gaps
)
from kernel.task_decomposition.types import WorldState
from kernel.validation.types import ErrorResponse


@pytest.mark.asyncio
@pytest.mark.parametrize("failed_val_data, macro_goal", [
    ({"error": "Missing database credentials", "type": "auth"}, "Sync production database with backup"),
    ({"error": "Unknown recipient email address", "field": "to"}, "Send quarterly report to the finance team"),
    ({}, "Just general exploration"),
    ({"error": "Model version mismatch", "expected": "v2", "got": "v1"}, "Run sentiment analysis on latest tweets")
])
async def test_curiosity_engine_comprehensive(failed_val_data, macro_goal, inference_kit):
    """REAL SIMULATION: Verify Curiosity Engine Kernel functions with multiple scenarios."""
    print(f"\n--- Testing Curiosity Engine: Goal='{macro_goal}', Data={failed_val_data} ---")

    world_state = WorldState(goal=macro_goal)
    from kernel.validation.types import ValidationGate
    error_resp = ErrorResponse(gate=ValidationGate.SYNTAX, message=failed_val_data.get("error", "none"), raw_data=failed_val_data)

    print("\n[Test]: detect_missing_variables")
    print(f"   [INPUT]: goal='{macro_goal}', error='{error_resp.message}'")
    gaps = detect_missing_variables(world_state, error_resp)
    assert isinstance(gaps, list)
    print(f"   [OUTPUT]: Missing Gaps count={len(gaps)}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: formulate_questions")
    print(f"   [INPUT]: {len(gaps)} gaps")
    questions = await formulate_questions(gaps, kit=inference_kit)
    assert isinstance(questions, list)
    print(f"   [OUTPUT]: Questions Formulated count={len(questions)}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: route_exploration_strategy")
    if questions:
        print(f"   [INPUT]: {len(questions)} questions")
        tasks = route_exploration_strategy(questions)
        assert len(tasks) == len(questions)
        print(f"   [OUTPUT]: Route Strategy -> Tasks count={len(tasks)}")
    else:
        print(f"   [INPUT]: No questions to route")
        print(f"   [OUTPUT]: Skipped strategy routing")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: explore_gaps")
    print(f"   [INPUT]: goal='{macro_goal}'")
    res = await explore_gaps(world_state, error_resp, kit=inference_kit)
    assert res.is_success
    print(f"   [OUTPUT]: Status={res.status}, Signals count={len(res.signals)}")
    print(" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
