from unittest.mock import AsyncMock, MagicMock

import pytest

from kernel.entity_recognition.types import ValidatedEntity
from kernel.intent_sentiment_urgency.types import IntentCategory, IntentLabel
from kernel.task_decomposition.engine import (
    analyze_goal_complexity,
    build_dependency_array,
    decompose_goal,
    split_into_sub_goals,
)
from kernel.task_decomposition.types import (
    ComplexityAssessment,
    ComplexityLevel,
    SubGoal,
    WorldState,
)
from shared.inference_kit import InferenceKit


@pytest.mark.asyncio
async def test_analyze_goal_complexity(monkeypatch):
    class MockSettings:
        complexity_atomic_threshold: int = 1
        complexity_compound_threshold: int = 3

    class MockKernelSettings:
        kernel = MockSettings()

    monkeypatch.setattr("kernel.task_decomposition.engine.get_settings", lambda: MockKernelSettings())

    # Atomic
    context = WorldState(goal="Create a file", context={}, knowledge_domains=["filesystem"])
    intent = IntentLabel(primary=IntentCategory.CREATE, confidence=0.9, candidates=[])
    entities = [ValidatedEntity(field_name="target", value="file")]

    res = await analyze_goal_complexity(context, intent, entities)
    assert res.level == ComplexityLevel.ATOMIC

    # Multi-domain
    context = WorldState(goal="Create a file and query the DB", context={}, knowledge_domains=["filesystem", "database"])
    entities = [
        ValidatedEntity(field_name="tgt1", value="file"),
        ValidatedEntity(field_name="tgt2", value="DB")
    ]
    res = await analyze_goal_complexity(context, intent, entities)
    assert res.level == ComplexityLevel.MULTI_DOMAIN


def test_split_into_sub_goals():
    assess = ComplexityAssessment(
        level=ComplexityLevel.COMPOUND,
        estimated_sub_tasks=2,
        primary_intent="UPDATE",
        entity_count=2,
        domains_involved=["general"],
        reasoning="",
    )

    sub_goals = split_into_sub_goals(assess)
    assert len(sub_goals) == 2
    assert sub_goals[0].outputs[0] == "output_0"
    assert sub_goals[1].inputs[0] == "output_0"


def test_build_dependency_array():
    goals = [
        SubGoal(id="g1", description="1", domain="d", inputs=[], outputs=["out1"]),
        SubGoal(id="g2", description="2", domain="d", inputs=["out1"], outputs=["out2"]),
        SubGoal(id="g3", description="3", domain="d", inputs=["out1"], outputs=["out3"]),
    ]

    graph = build_dependency_array(goals)

    assert len(graph.edges) == 2
    # parallel groups should group g2 and g3
    assert ["g2", "g3"] in graph.parallel_groups or ["g3", "g2"] in graph.parallel_groups


@pytest.mark.asyncio
async def test_llm_fallback_decompose_goal(monkeypatch):
    class MockSettings:
        complexity_atomic_threshold: int = 1
        complexity_compound_threshold: int = 3

    class MockKernelSettings:
        kernel = MockSettings()

    monkeypatch.setattr("kernel.task_decomposition.engine.get_settings", lambda: MockKernelSettings())

    kit = MagicMock(spec=InferenceKit)
    kit.has_llm = True

    mock_resp = MagicMock()
    mock_resp.content = '```json\n[{"id": "t1", "description": "do it", "domain": "gen", "required_skills": [], "required_tools": [], "depends_on": [], "inputs": [], "outputs": [], "parallelizable": false}]\n```'

    kit.llm = AsyncMock()
    kit.llm.complete.return_value = mock_resp
    kit.llm_config = MagicMock()

    context = WorldState(goal="Do it", context={}, knowledge_domains=["gen"])

    res = await decompose_goal(context, kit=kit)
    assert res.is_success

    data = res.unwrap()
    assert len(data.signals) == 1
    tasks = data.signals[0].body["data"]
    assert len(tasks) == 1
    assert tasks[0]["id"] == "t1"
