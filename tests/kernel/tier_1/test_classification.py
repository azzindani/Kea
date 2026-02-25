from unittest.mock import AsyncMock, MagicMock

import pytest

from kernel.classification.engine import (
    classify,
    merge_classification_layers,
    run_linguistic_analysis,
)
from kernel.classification.types import (
    ClassificationResult,
    ClassProfileRules,
    LabelScore,
    LinguisticResult,
    PatternRule,
    SemanticResult,
)
from shared.inference_kit import InferenceKit


def test_run_linguistic_analysis():
    rules = ClassProfileRules(
        name="test_profile",
        description="Testing profile",
        pattern_rules=[
            PatternRule(label="SUPPORT", pattern=r"\b(help|issue|broken)\b", weight=1.0),
        ],
        pos_rules=[],
    )

    res = run_linguistic_analysis("My system is broken", rules)
    assert len(res.candidates) > 0
    assert res.candidates[0].label == "SUPPORT"


def test_merge_classification_layers(monkeypatch):
    class MockSettings:
        classification_linguistic_weight: float = 0.5
        classification_semantic_weight: float = 0.5

    class MockKernelSettings:
        kernel = MockSettings()

    monkeypatch.setattr("kernel.classification.engine.get_settings", lambda: MockKernelSettings())

    ling = LinguisticResult(
        candidates=[LabelScore(label="SUPPORT", score=0.8)],
        matched_patterns=["help"],
        matched_pos_tags=[],
    )

    sem = SemanticResult(
        candidates=[LabelScore(label="SUPPORT", score=0.9)],
        embedding_used=True,
    )

    # Merge should pass threshold
    res = merge_classification_layers(ling, sem, threshold=0.5)

    assert isinstance(res, ClassificationResult)
    assert res.top_label == "SUPPORT"
    assert res.confidence > 0.5


@pytest.mark.asyncio
async def test_llm_fallback_classify():
    rules = ClassProfileRules(name="test", description="desc", pattern_rules=[], pos_rules=[])
    kit = MagicMock(spec=InferenceKit)
    kit.has_llm = True

    mock_resp = MagicMock()
    mock_resp.content = '```json\n{"category": "SALES", "confidence": 0.90, "reasoning": "mentions buying"}\n```'

    kit.llm = AsyncMock()
    kit.llm.complete.return_value = mock_resp
    kit.llm_config = MagicMock()

    # The heuristic will fail because there are no rule matches, so it falls back to the LLM
    res = await classify("I want to buy something", rules, kit)
    assert res.is_success

    data = res.unwrap()
    payload = data.signals[0].body["data"]
    assert payload["top_label"] == "SALES"
    assert payload["confidence"] == 0.90
