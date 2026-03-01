from unittest.mock import AsyncMock, MagicMock

import pytest

from kernel.hallucination_monitor.engine import (
    calculate_grounding_score,
    classify_claims,
    grade_claim,
)
from kernel.hallucination_monitor.types import Claim, ClaimGradeLevel, ClaimType, Origin
from shared.inference_kit import InferenceKit


@pytest.mark.asyncio
async def test_classify_claims():
    text = "The sky is blue. I think it will rain today. Therefore, we should take an umbrella."
    claims = await classify_claims(text)

    assert len(claims) == 3
    assert claims[0].claim_type == ClaimType.FACTUAL
    assert claims[1].claim_type == ClaimType.OPINION
    assert claims[2].claim_type == ClaimType.REASONING


@pytest.mark.asyncio
async def test_grade_claim(monkeypatch):
    class MockSettings:
        grounding_similarity_threshold: float = 0.5
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.hallucination_monitor.engine.get_settings", lambda: MockKernelSettings())

    # Factual match
    claim1 = Claim(claim_id="c1", text="The sky is blue", claim_type=ClaimType.FACTUAL, source_sentence="", position=0)
    ev1 = Origin(origin_id="o1", source_type="", reference="", content="The sky is very blue today, with some clouds.", confidence=1.0)
    grade1 = await grade_claim(claim1, [ev1])
    assert grade1.grade == ClaimGradeLevel.GROUNDED

    # Opinion is auto grounded
    claim2 = Claim(claim_id="c2", text="I like blue", claim_type=ClaimType.OPINION, source_sentence="", position=0)
    grade2 = await grade_claim(claim2, [ev1])
    assert grade2.grade == ClaimGradeLevel.GROUNDED

    # Fabricated
    claim3 = Claim(claim_id="c3", text="The grass is red", claim_type=ClaimType.FACTUAL, source_sentence="", position=0)
    grade3 = await grade_claim(claim3, [ev1])
    assert grade3.grade == ClaimGradeLevel.FABRICATED


def test_calculate_grounding_score(monkeypatch):
    class MockSettings:
        grounding_grounded_weight: float = 1.0
        grounding_inferred_weight: float = 0.5
        grounding_fabricated_weight: float = 0.0
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.hallucination_monitor.engine.get_settings", lambda: MockKernelSettings())

    grade1 = MagicMock()
    grade1.grade = ClaimGradeLevel.GROUNDED
    grade1.best_similarity = 1.0

    grade2 = MagicMock()
    grade2.grade = ClaimGradeLevel.FABRICATED
    grade2.best_similarity = 0.0

    score = calculate_grounding_score([grade1, grade2])
    assert score == 0.5


@pytest.mark.asyncio
async def test_llm_fallback_classify_claims():
    kit = MagicMock(spec=InferenceKit)
    kit.has_llm = True

    mock_resp = MagicMock()
    mock_resp.content = '```json\n[{"text": "LLM claim", "claim_type": "FACTUAL"}]\n```'

    kit.llm = AsyncMock()
    kit.llm.complete.return_value = mock_resp
    kit.llm_config = MagicMock()

    claims = await classify_claims("Some text", kit=kit)
    assert len(claims) == 1
    assert claims[0].text == "LLM claim"
    assert claims[0].claim_type == ClaimType.FACTUAL
