from unittest.mock import AsyncMock, MagicMock

import pytest

from kernel.curiosity_engine.engine import (
    detect_missing_variables,
    explore_gaps,
    formulate_questions,
    route_exploration_strategy,
)
from kernel.curiosity_engine.types import (
    ExplorationQuery,
    ExplorationStrategy,
    KnowledgeGap,
)
from kernel.task_decomposition.types import WorldState
from kernel.validation.types import ErrorResponse, ValidationGate
from shared.inference_kit import InferenceKit


def test_detect_missing_variables():
    task_state = WorldState(goal="Create account", context={"name": "Alice"}, knowledge_domains=[])
    validation_error = ErrorResponse(
        gate=ValidationGate.STRUCTURE,
        message="Missing keys: 'email', 'age'.",
    )

    gaps = detect_missing_variables(task_state, validation_error)
    assert len(gaps) == 2

    fields = [g.field_name for g in gaps]
    assert "email" in fields
    assert "age" in fields


@pytest.mark.asyncio
async def test_formulate_questions(monkeypatch):
    class MockSettings:
        curiosity_strategy_mappings: dict[str, str] = {
            "web": "web",
            "search": "rag",
            "scan": "scan"
        }

    class MockKernelSettings:
        kernel = MockSettings()

    monkeypatch.setattr("kernel.curiosity_engine.engine.get_settings", lambda: MockKernelSettings())

    gaps = [
        KnowledgeGap(field_name="email", expected_type="unknown", importance=0.8, context="Find via search"),
        KnowledgeGap(field_name="age", expected_type="unknown", importance=0.5, context="Look on the web"),
    ]

    queries = await formulate_questions(gaps)
    assert len(queries) == 2
    assert "email" in queries[0].query_text

    strategies = [q.strategy_hint for q in queries]
    assert ExplorationStrategy.RAG in strategies
    assert ExplorationStrategy.WEB in strategies


def test_route_exploration_strategy():
    queries = [
        ExplorationQuery(
            gap=KnowledgeGap(field_name="email", expected_type="unknown", importance=0.8, context=""),
            query_text="Find email",
            strategy_hint=ExplorationStrategy.RAG
        ),
        ExplorationQuery(
            gap=KnowledgeGap(field_name="age", expected_type="unknown", importance=0.5, context=""),
            query_text="Find age",
            strategy_hint=ExplorationStrategy.WEB
        ),
    ]

    tasks = route_exploration_strategy(queries)
    assert len(tasks) == 2
    assert tasks[0].target_service == "rag_service"
    assert tasks[1].target_service == "gateway"


@pytest.mark.asyncio
async def test_llm_fallback_explore_gaps(monkeypatch):
    class MockSettings:
        curiosity_strategy_mappings: dict[str, str] = {}
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.curiosity_engine.engine.get_settings", lambda: MockKernelSettings())

    kit = MagicMock(spec=InferenceKit)
    kit.has_llm = True

    mock_resp = MagicMock()
    # Mock LLM query refinement
    mock_resp.content = '```json\n{"query": "Highly refined search query"}\n```'

    kit.llm = AsyncMock()
    kit.llm.complete.return_value = mock_resp
    kit.llm_config = MagicMock()

    task_state = WorldState(goal="Test LLM", context={}, knowledge_domains=[])
    validation_error = ErrorResponse(gate=ValidationGate.STRUCTURE, message="Missing keys: 'data'")

    res = await explore_gaps(task_state, validation_error, kit=kit)
    assert res.is_success

    data = res.unwrap()
    assert len(data.signals) == 1
    tasks = data.signals[0].body["data"]
    assert len(tasks) == 1

    # Check that LLM refined query was applied
    assert tasks[0]["query"] == "Highly refined search query"
