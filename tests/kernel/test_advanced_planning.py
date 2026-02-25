import pytest

from kernel.advanced_planning.engine import (
    sequence_subtasks,
    prioritize_tasks,
    bind_tools_to_tasks,
    generate_outcome_hypotheses,
    inject_progress_tracker,
    run_advanced_planning
)
from kernel.task_decomposition.types import SubTaskItem
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("subtasks_data", [
    # Scenario 1: Single task
    [SubTaskItem(id="t1", description="Search Apple price", domain="finance", required_skills=["finance"], required_tools=["web"], depends_on=[], inputs=[], outputs=["price"], parallelizable=True)],
    # Scenario 2: Multiple tasks with dependencies
    [
        SubTaskItem(id="t1", description="Get data", domain="data", required_skills=["sql"], required_tools=["db"], depends_on=[], inputs=[], outputs=["raw"], parallelizable=True),
        SubTaskItem(id="t2", description="Process data", domain="data", required_skills=["python"], required_tools=["repl"], depends_on=["t1"], inputs=["raw"], outputs=["clean"], parallelizable=False),
        SubTaskItem(id="t3", description="Notify user", domain="comm", required_skills=[], required_tools=["email"], depends_on=["t2"], inputs=["clean"], outputs=["done"], parallelizable=True)
    ],
    # Scenario 3: Empty (Edge case)
    []
])
async def test_advanced_planning_comprehensive(subtasks_data):
    """REAL SIMULATION: Verify Advanced Planning Kernel functions with multiple inputs."""
    print(f"\n--- Testing Advanced Planning with {len(subtasks_data)} Subtasks ---")

    print(f"\n[Test]: sequence_subtasks")
    sequenced = sequence_subtasks(subtasks_data)
    assert len(sequenced) == len(subtasks_data)
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: prioritize_tasks")
    prioritized = prioritize_tasks(sequenced)
    assert len(prioritized) == len(subtasks_data)
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: bind_tools_to_tasks")
    bound = await bind_tools_to_tasks(prioritized)
    assert len(bound) == len(subtasks_data)
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: generate_outcome_hypotheses")
    hypothesized = await generate_outcome_hypotheses(bound, kit=None)
    assert len(hypothesized) == len(subtasks_data)
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: inject_progress_tracker")
    tracked_plan = inject_progress_tracker(hypothesized)
    assert len(tracked_plan.tasks) == len(subtasks_data)
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: run_advanced_planning")
    res = await run_advanced_planning(subtasks_data, kit=None)
    assert res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
