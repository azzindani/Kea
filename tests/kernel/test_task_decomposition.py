import pytest

from kernel.task_decomposition.engine import (
    analyze_goal_complexity,
    split_into_sub_goals,
    build_dependency_array,
    map_required_skills,
    decompose_goal
)
from kernel.task_decomposition.types import WorldState
from kernel.intent_sentiment_urgency.types import IntentLabel, IntentCategory
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("high_level_goal", [
    "Find the current price of Bitcoin and send an email alert if it is above $60k.",
    "Draft a research paper on the impact of AI on corporate governance.",
    "Hello system.",
    "Initialize the production database, migrate the old schema, and verify the data integrity.",
    ""
])
async def test_task_decomposition_comprehensive(high_level_goal):
    """REAL SIMULATION: Verify Task Decomposition Kernel functions with multiple goals."""
    print(f"\n--- Testing Task Decomposition: Goal='{high_level_goal}' ---")

    ws = WorldState(goal=high_level_goal)
    intent = IntentLabel(primary=IntentCategory.QUERY, confidence=1.0)

    print(f"\n[Test]: analyze_goal_complexity")
    complexity_assessment = await analyze_goal_complexity(ws, intent, entities=[])
    assert complexity_assessment is not None
    print(f"   Complexity Level: {complexity_assessment.level}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: split_into_sub_goals")
    sub_goals = split_into_sub_goals(complexity_assessment)
    assert isinstance(sub_goals, list)
    print(f"   Sub-goals generated: {len(sub_goals)}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: build_dependency_array")
    dependency_graph = build_dependency_array(sub_goals)
    assert dependency_graph is not None
    print(f"   Dependency relations mapped")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: map_required_skills")
    map_required_skills(sub_goals, dependency_graph)
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: decompose_goal")
    res = await decompose_goal(ws, kit=None)
    assert res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
