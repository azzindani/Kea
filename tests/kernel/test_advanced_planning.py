import pytest

from kernel.advanced_planning.engine import (
    sequence_and_prioritize,
    bind_tools,
    generate_hypotheses,
    inject_progress_tracker,
    plan_advanced
)
from kernel.advanced_planning.types import (
    PlanningConstraints,
    MCPToolRegistry,
    PriorityMode
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
async def test_advanced_planning_comprehensive(subtasks_data, inference_kit):
    """REAL SIMULATION: Verify Advanced Planning Kernel functions with multiple inputs."""
    print(f"\n--- Testing Advanced Planning with {len(subtasks_data)} Subtasks ---")

    constraints = PlanningConstraints(priority_mode=PriorityMode.BALANCED)
    registry = MCPToolRegistry()

    print(f"\n[Test]: sequence_and_prioritize")
    print(f"   [INPUT]: {len(subtasks_data)} subtasks")
    sequenced = await sequence_and_prioritize(subtasks_data, constraints)
    assert len(sequenced) == len(subtasks_data)
    print(f"   [OUTPUT]: Sequenced {len(sequenced)} tasks")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: bind_tools")
    print(f"   [INPUT]: {len(sequenced)} tasks")
    bound = await bind_tools(sequenced, registry)
    assert len(bound) == len(subtasks_data)
    print(f"   [OUTPUT]: Tools bound to {len(bound)} tasks")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: generate_hypotheses")
    print(f"   [INPUT]: {len(bound)} bound tasks")
    hypotheses = generate_hypotheses(bound)
    assert len(hypotheses) <= len(subtasks_data)
    print(f"   [OUTPUT]: Generated {len(hypotheses)} hypotheses")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: inject_progress_tracker")
    print(f"   [INPUT]: {len(bound)} tasks, {len(hypotheses)} hypotheses")
    tracked_plan = inject_progress_tracker(bound, hypotheses, constraints)
    assert len(tracked_plan.tasks) == len(subtasks_data)
    print(f"   [OUTPUT]: Progress tracker injected")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: plan_advanced")
    print(f"   [INPUT]: {len(subtasks_data)} subtasks")
    res = await plan_advanced(subtasks_data, kit=inference_kit)
    assert res.is_success
    print(f"   [OUTPUT]: Status={res.status}, Signals count={len(res.signals)}")
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
