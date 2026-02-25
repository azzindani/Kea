import pytest

from kernel.curiosity_engine.engine import (
    identify_missing_info,
    formulate_investigation_questions,
    select_exploration_strategy,
    run_curiosity_engine
)
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("failed_val_data, macro_goal", [
    ({"error": "Missing database credentials", "type": "auth"}, "Sync production database with backup"),
    ({"error": "Unknown recipient email address", "field": "to"}, "Send quarterly report to the finance team"),
    ({}, "Just general exploration"),
    ({"error": "Model version mismatch", "expected": "v2", "got": "v1"}, "Run sentiment analysis on latest tweets")
])
async def test_curiosity_engine_comprehensive(failed_val_data, macro_goal):
    """REAL SIMULATION: Verify Curiosity Engine Kernel functions with multiple scenarios."""
    print(f"\n--- Testing Curiosity Engine: Goal='{macro_goal}', Data={failed_val_data} ---")

    print(f"\n[Test]: identify_missing_info")
    missing_info_list = identify_missing_info(failed_val_data)
    assert isinstance(missing_info_list, list)
    print(f"   Missing Information: {missing_info_list}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: formulate_investigation_questions")
    questions = await formulate_investigation_questions(missing_info_list, macro_goal, kit=None)
    assert isinstance(questions, list)
    print(f"   Questions Formulated: {len(questions)}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: select_exploration_strategy")
    if questions:
        for q in questions:
            strategy = select_exploration_strategy(q)
            assert strategy is not None
            assert hasattr(strategy, 'strategy_id')
            print(f"   Question '{q[:20]}...' -> Strategy: {strategy.strategy_id}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: run_curiosity_engine")
    res = await run_curiosity_engine(failed_val_data, macro_goal, kit=None)
    assert res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
