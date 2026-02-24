from unittest.mock import AsyncMock, MagicMock

import pytest

from kernel.intent_sentiment_urgency.engine import (
    analyze_sentiment,
    detect_intent,
    detect_intent_async,
    score_urgency,
)
from kernel.intent_sentiment_urgency.types import (
    IntentCategory,
    SentimentCategory,
    UrgencyBand,
)
from shared.inference_kit import InferenceKit


@pytest.mark.asyncio
async def test_detect_intent_heuristics():
    # Test CREATE intent
    res = detect_intent("Please create a new file for me")
    assert res.primary == IntentCategory.CREATE

    # Test DELETE intent
    res = detect_intent("Can you delete the old configuration?")
    assert res.primary == IntentCategory.DELETE

    # Test UNKNOWN/Fallback
    res = detect_intent("Just saying hello!")
    assert res.primary == IntentCategory.UNKNOWN


@pytest.mark.asyncio
async def test_analyze_sentiment_heuristics():
    # Positive
    res = analyze_sentiment("This is absolutely wonderful and great!")
    assert res.primary == SentimentCategory.POSITIVE
    assert res.valence > 0.0

    # Negative
    res = analyze_sentiment("This is a terrible and awful problem.")
    assert res.primary == SentimentCategory.NEGATIVE
    assert res.valence < 0.0

    # Frustrated
    res = analyze_sentiment("Why is this terrible bug still happening again?")
    assert res.primary == SentimentCategory.FRUSTRATED


def test_score_urgency_heuristics(monkeypatch):
    # Mock settings since it relies on get_settings()
    class MockSettings:
        urgency_keywords_critical = ["emergency", "critical", "outage"]
        urgency_keywords_high = ["urgent", "asap", "quickly"]
        urgency_keywords_low = ["whenever", "no rush"]

    class MockKernelSettings:
        kernel = MockSettings()

    monkeypatch.setattr("kernel.intent_sentiment_urgency.engine.get_settings", lambda: MockKernelSettings())

    # Normal urgency
    res = score_urgency("Please update the docs.")
    assert res.band in [UrgencyBand.NORMAL, UrgencyBand.LOW]

    # Critical urgency
    res = score_urgency("EMERGENCY! The system is facing an outage!")
    assert res.band == UrgencyBand.CRITICAL


@pytest.mark.asyncio
async def test_llm_fallback_detect_intent():
    kit = MagicMock(spec=InferenceKit)
    kit.has_llm = True

    mock_resp = MagicMock()
    mock_resp.content = '```json\n{"intent": "QUERY", "confidence": 0.95}\n```'

    kit.llm = AsyncMock()
    kit.llm.complete.return_value = mock_resp
    kit.llm_config = MagicMock()

    # Confusing text that heuristics alone won't get easily
    text = "I'm looking around for some information"
    res = await detect_intent_async(text, kit=kit)

    # Assert LLM was called and correctly parsed
    assert res.primary == IntentCategory.QUERY
    assert res.confidence == 0.95
    kit.llm.complete.assert_called_once()
