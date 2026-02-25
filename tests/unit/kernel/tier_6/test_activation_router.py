from unittest.mock import AsyncMock, MagicMock

import pytest

from kernel.activation_router.engine import (
    cache_decision,
    check_decision_cache,
    classify_signal_complexity,
    select_pipeline,
)
from kernel.activation_router.types import (
    ComplexityLevel,
)
from kernel.self_model.types import SignalTags
from shared.inference_kit import InferenceKit


@pytest.mark.asyncio
async def test_classify_signal_complexity(monkeypatch):
    class MockSettings:
        activation_urgency_weight: float = 0.3
        activation_structural_weight: float = 0.25
        activation_domain_weight: float = 0.25
        activation_gap_weight: float = 0.2
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.activation_router.engine.get_settings", lambda: MockKernelSettings())

    tags = SignalTags(
        domain="general",
        required_tools=[],
        required_skills=[],
        urgency="low",
        complexity="trivial",
    )
    # Very low scores -> TRIVIAL
    lvl = await classify_signal_complexity(tags)
    assert lvl == ComplexityLevel.TRIVIAL

    # Critical urgency bypasses
    tags2 = SignalTags(
        domain="general",
        required_tools=[],
        required_skills=[],
        urgency="critical",
        complexity="trivial",
    )
    lvl2 = await classify_signal_complexity(tags2)
    assert lvl2 == ComplexityLevel.CRITICAL


def test_select_pipeline(monkeypatch):
    class MockSettings:
        activation_pressure_moderate: float = 0.6
        activation_pressure_high: float = 0.8
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.activation_router.engine.get_settings", lambda: MockKernelSettings())

    # Normal
    p1 = select_pipeline(ComplexityLevel.COMPLEX, 0.0)
    assert p1.complexity_level == ComplexityLevel.COMPLEX

    # Moderate pressure -> downgrade 1 level (COMPLEX -> MODERATE)
    p2 = select_pipeline(ComplexityLevel.COMPLEX, 0.7)
    assert p2.complexity_level == ComplexityLevel.MODERATE


def test_decision_cache(monkeypatch):
    class MockSettings:
        activation_cache_ttl_seconds: int = 60
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.activation_router.engine.get_settings", lambda: MockKernelSettings())

    tags = SignalTags(domain="test", required_tools=[], required_skills=[], urgency="low", complexity="simple")

    # Empty
    assert check_decision_cache(tags) is None

    # Store
    amap = MagicMock()
    amap.model_copy.return_value = "cached_val"
    cache_decision(tags, amap)

    # Hit
    cached = check_decision_cache(tags)
    assert cached == "cached_val"


@pytest.mark.asyncio
async def test_llm_fallback_complexity(monkeypatch):
    kit = MagicMock(spec=InferenceKit)
    kit.has_llm = True

    mock_resp = MagicMock()
    mock_resp.content = '```json\n{"level": "CRITICAL"}\n```'

    kit.llm = AsyncMock()
    kit.llm.complete.return_value = mock_resp
    kit.llm_config = MagicMock()

    tags = SignalTags(domain="general", required_tools=[], required_skills=[], urgency="low", complexity="trivial")
    lvl = await classify_signal_complexity(tags, kit=kit)

    assert lvl == ComplexityLevel.CRITICAL
