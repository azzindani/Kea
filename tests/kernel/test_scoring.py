import pytest

from kernel.scoring.engine import (
    calculate_priority_score,
    calculate_readiness_score,
    run_task_scoring
)
from kernel.graph_synthesizer.types import ExecutableNode, ActionInstruction
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("task_desc, urgency_val, deps_met", [
    ("Critical system recovery", 0.99, True),
    ("Minor stylistic adjustment", 0.10, True),
    ("Wait for user approval", 0.80, False),
    ("Background data indexing", 0.40, True),
    ("Emergency shutdown", 1.0, True)
])
async def test_scoring_comprehensive(task_desc, urgency_val, deps_met):
    """REAL SIMULATION: Verify Scoring Kernel functions with multiple task profiles."""
    print(f"\n--- Testing Scoring: Task='{task_desc}', Urgency={urgency_val}, Deps Met={deps_met} ---")

    node = ExecutableNode(
        node_id="n-001",
        instruction=ActionInstruction(task_id="t-001", description=task_desc, action_type="generic", parameters={}),
        input_keys=[],
        output_keys=[],
        input_schema="dict",
        output_schema="dict"
    )

    print(f"\n[Test]: calculate_priority_score")
    priority_score = calculate_priority_score(node, urgency_val)
    assert 0.0 <= priority_score <= 1.0
    print(f"   Priority Score: {priority_score:.2f}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: calculate_readiness_score")
    readiness_score = calculate_readiness_score(node, deps_met)
    assert 0.0 <= readiness_score <= 1.0
    print(f"   Readiness Score: {readiness_score:.2f}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: run_task_scoring")
    res = await run_task_scoring(node, urgency_val, deps_met)
    assert res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
