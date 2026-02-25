from unittest.mock import AsyncMock, MagicMock

import pytest

from kernel.task_decomposition.types import WorldState
from kernel.what_if_scenario.engine import (
    calculate_risk_reward,
    generate_outcome_branches,
    predict_consequences,
)
from kernel.what_if_scenario.types import (
    CompiledDAG,
    ConsequencePrediction,
    OutcomeBranch,
    VerdictDecision,
)
from shared.inference_kit import InferenceKit


def test_generate_outcome_branches(monkeypatch):
    class MockSettings:
        max_simulation_branches: int = 4
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.what_if_scenario.engine.get_settings", lambda: MockKernelSettings())

    action = CompiledDAG(
        id="dag1",
        description="Complex external task",
        nodes=["n1", "n2", "n3"],
        edges=[],
        has_external_calls=True
    )
    knowledge = WorldState(goal="Test", context={}, knowledge_domains=[])

    branches = generate_outcome_branches(action, knowledge)

    assert len(branches) == 4
    success_branches = [b for b in branches if b.is_success]
    assert len(success_branches) == 1

    paths = [b.path_steps for b in branches]
    assert any("Timeout after retry" in p[-1] for p in paths if len(p) > 1)


@pytest.mark.asyncio
async def test_predict_consequences():
    branches = [
        OutcomeBranch(
            branch_id="b1",
            description="Success",
            is_success=True,
            likelihood=0.8,
            terminal_state="Done",
            path_steps=["Execute n1", "Execute n2"]
        ),
        OutcomeBranch(
            branch_id="b2",
            description="Error during execution! EMERGENCY stop required!",
            is_success=False,
            likelihood=0.2,
            terminal_state="Failed",
            path_steps=["Execute n1", "Error"]
        )
    ]

    # We pass it without LLM kit so it falls back to heuristics
    preds = await predict_consequences(branches)

    assert len(preds) == 2
    b1_pred = next(p for p in preds if p.branch_id == "b1")
    b2_pred = next(p for p in preds if p.branch_id == "b2")

    assert b1_pred.severity_score == 0.0
    assert b2_pred.severity_score > 0.0
    assert not b2_pred.reversible


def test_calculate_risk_reward(monkeypatch):
    class MockSettings:
        risk_threshold_approve: float = 0.3
        risk_threshold_reject: float = 0.7
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.what_if_scenario.engine.get_settings", lambda: MockKernelSettings())

    preds = [ConsequencePrediction(branch_id="b1", resource_impact="low", state_mutations=[], reversible=True, severity_score=0.1, external_impacts=[])]
    verdict = calculate_risk_reward(preds)
    assert verdict.decision == VerdictDecision.APPROVE

    preds_reject = [ConsequencePrediction(branch_id="b1", resource_impact="high", state_mutations=[], reversible=False, severity_score=1.5, external_impacts=[])]
    verdict_reject = calculate_risk_reward(preds_reject)
    assert verdict_reject.decision == VerdictDecision.REJECT


@pytest.mark.asyncio
async def test_llm_fallback_predict_consequences():
    kit = MagicMock(spec=InferenceKit)
    kit.has_llm = True

    mock_resp = MagicMock()
    mock_resp.content = '```json\n{"resource_impact": "high", "state_mutations": ["Auth DB updated"], "external_impacts": ["Send email"]}\n```'

    kit.llm = AsyncMock()
    kit.llm.complete.return_value = mock_resp
    kit.llm_config = MagicMock()

    branches = [OutcomeBranch(branch_id="b1", description="Success", is_success=True, likelihood=0.8, terminal_state="", path_steps=[])]
    preds = await predict_consequences(branches, kit=kit)

    assert len(preds) == 1
    assert preds[0].resource_impact == "high"
    assert "Auth DB updated" in preds[0].state_mutations
    assert "Send email" in preds[0].external_impacts
