from unittest.mock import AsyncMock, MagicMock

import pytest

from kernel.attention_and_plausibility.engine import (
    check_plausibility,
    filter_attention,
)
from kernel.attention_and_plausibility.types import (
    ContextElement,
    FilteredState,
    PlausibilityVerdict,
    TaskState,
)
from shared.inference_kit import InferenceKit


@pytest.mark.asyncio
async def test_filter_attention(monkeypatch):
    class MockSettings:
        attention_relevance_threshold: float = 0.5
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.attention_and_plausibility.engine.get_settings", lambda: MockKernelSettings())

    async def mock_sim(content: str, query: str) -> float:
        if "relevant" in content:
            return 0.9
        return 0.1

    monkeypatch.setattr("kernel.attention_and_plausibility.engine.compute_semantic_similarity", mock_sim)

    elements = [
        ContextElement(key="test1", value="highly relevant context", source="test"),
        ContextElement(key="test2", value="completely random noise", source="test"),
    ]

    state = TaskState(goal="Do the thing", context_elements=elements)
    filtered = await filter_attention(state)

    assert len(filtered.critical_elements) == 1
    assert filtered.dropped_count == 1
    assert filtered.critical_elements[0].relevance == 0.9


@pytest.mark.asyncio
async def test_check_plausibility(monkeypatch):
    class MockSettings:
        plausibility_confidence_threshold: float = 0.5
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.attention_and_plausibility.engine.get_settings", lambda: MockKernelSettings())

    # Contradiction pattern
    filtered = FilteredState(goal="create and destroy constraints", critical_elements=[], dropped_count=0)

    # We bypass LLM by default
    res = await check_plausibility(filtered)

    assert len(res.issues) > 0
    assert any("Contradictory" in issue for issue in res.issues)
    assert res.verdict == PlausibilityVerdict.FAIL


@pytest.mark.asyncio
async def test_llm_fallback_plausibility(monkeypatch):
    class MockSettings:
        plausibility_confidence_threshold: float = 0.5
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.attention_and_plausibility.engine.get_settings", lambda: MockKernelSettings())

    kit = MagicMock(spec=InferenceKit)
    kit.has_llm = True

    mock_resp = MagicMock()
    mock_resp.content = '```json\n{"is_plausible": false, "issues": ["Magic is not real"]}\n```'

    kit.llm = AsyncMock()
    kit.llm.complete.return_value = mock_resp
    kit.llm_config = MagicMock()

    filtered = FilteredState(goal="Cast a fire spell", critical_elements=[], dropped_count=0)

    res = await check_plausibility(filtered, kit=kit)
    assert any("Magic is not real" in issue for issue in res.issues)
