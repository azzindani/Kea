from unittest.mock import AsyncMock, MagicMock

import pytest

from kernel.advanced_planning.engine import (
    bind_tools,
    generate_hypotheses,
    sequence_and_prioritize,
)
from kernel.advanced_planning.types import (
    BoundTask,
    MCPTool,
    MCPToolRegistry,
    PlanningConstraints,
    PriorityMode,
    SequencedTask,
)
from kernel.task_decomposition.types import SubTaskItem
from shared.inference_kit import InferenceKit


@pytest.mark.asyncio
async def test_sequence_and_prioritize(monkeypatch):
    class MockSettings:
        planning_speed_weight: float = 0.3
        planning_cost_weight: float = 0.3
        planning_fidelity_weight: float = 0.4
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.advanced_planning.engine.get_settings", lambda: MockKernelSettings())

    tasks = [
        SubTaskItem(id="t1", description="Cheap but slow", domain="", required_skills=[], required_tools=[], depends_on=["t2"], inputs=[], outputs=[], parallelizable=False),
        SubTaskItem(id="t2", description="Expensive but fast", domain="", required_skills=[], required_tools=["expensive_tool", "another_tool"], depends_on=[], inputs=[], outputs=[], parallelizable=False)
    ]

    constraints = PlanningConstraints(priority_mode=PriorityMode.SPEED)
    seq = await sequence_and_prioritize(tasks, constraints)

    assert len(seq) == 2


@pytest.mark.asyncio
async def test_bind_tools():
    tasks = [
        SequencedTask(task_id="t1", description="", priority_rank=1, estimated_cost=0.0, estimated_duration_ms=0.0, parallelizable=False, depends_on=[], inputs=[], outputs=[], domain="gen", required_skills=[], required_tools=["database_query"])
    ]

    registry = MCPToolRegistry(tools=[
        MCPTool(tool_id="db1", tool_name="sqlite_database_query_tool", description="", compatibility_score=1.0),
        MCPTool(tool_id="web1", tool_name="web_search", description="", compatibility_score=1.0)
    ])

    bound = await bind_tools(tasks, registry)

    assert len(bound) == 1
    assert bound[0].tool_binding is not None
    assert bound[0].tool_binding.tool_id == "db1"


def test_generate_hypotheses(monkeypatch):
    class MockSettings:
        max_hypothesis_count: int = 5
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.advanced_planning.engine.get_settings", lambda: MockKernelSettings())

    tasks = [
        BoundTask(task_id="t1", description="Success check", priority_rank=1, estimated_cost=0.0, estimated_duration_ms=0.0, parallelizable=False, depends_on=[], inputs=[], outputs=["result"], domain="gen", tool_binding=None)
    ]

    hypos = generate_hypotheses(tasks)

    assert len(hypos) == 1
    assert "result" in hypos[0].success_criteria


@pytest.mark.asyncio
async def test_llm_fallback_sequence(monkeypatch):
    class MockSettings:
        planning_speed_weight: float = 0.3
        planning_cost_weight: float = 0.3
        planning_fidelity_weight: float = 0.4
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.advanced_planning.engine.get_settings", lambda: MockKernelSettings())

    kit = MagicMock(spec=InferenceKit)
    kit.has_llm = True

    mock_resp = MagicMock()
    mock_resp.content = '```json\n{"cost": 0.9, "duration_ms": 5000.0}\n```'

    kit.llm = AsyncMock()
    kit.llm.complete.return_value = mock_resp
    kit.llm_config = MagicMock()

    tasks = [
        SubTaskItem(id="t1", description="", domain="", required_skills=[], required_tools=[], depends_on=[], inputs=[], outputs=[], parallelizable=False)
    ]

    constraints = PlanningConstraints(priority_mode=PriorityMode.BALANCED)
    seq = await sequence_and_prioritize(tasks, constraints, kit=kit)

    assert len(seq) == 1
    assert seq[0].estimated_cost == 0.9
    assert seq[0].estimated_duration_ms == 5000.0
