import pytest

from kernel.task_decomposition.engine import (
    analyze_goal_complexity,
    split_goal_to_subtasks,
    build_dependency_array,
    map_required_skills,
    run_task_decomposition
)
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

    print(f"\n[Test]: analyze_goal_complexity")
    complexity_score = await analyze_goal_complexity(high_level_goal, kit=None)
    assert complexity_score >= 0
    print(f"   Complexity Score: {complexity_score}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: split_goal_to_subtasks")
    subtasks = await split_goal_to_subtasks(high_level_goal, complexity_score, kit=None)
    assert isinstance(subtasks, list)
    print(f"   Subtasks generated: {len(subtasks)}")
    for t in subtasks:
        print(f"     - {t.description} (Domain: {t.domain})")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: build_dependency_array")
    dependency_map = build_dependency_array(subtasks)
    assert isinstance(dependency_map, dict)
    print(f"   Dependency relations mapped: {len(dependency_map)}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: map_required_skills")
    required_skills = map_required_skills(subtasks)
    assert isinstance(required_skills, set)
    print(f"   Skills needed: {required_skills}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: run_task_decomposition")
    res = await run_task_decomposition(high_level_goal, kit=None)
    assert res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
