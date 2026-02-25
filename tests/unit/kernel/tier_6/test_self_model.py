from unittest.mock import AsyncMock, MagicMock

import pytest

from kernel.lifecycle_controller.types import IdentityContext
from kernel.self_model.engine import (
    detect_capability_gap,
    get_calibration_history,
    get_current_state,
    refresh_capability_map,
    update_accuracy_history,
    update_cognitive_state,
)
from kernel.self_model.types import ProcessingPhase, SignalTags
from shared.inference_kit import InferenceKit


@pytest.mark.asyncio
async def test_detect_capability_gap():
    await refresh_capability_map()

    identity = IdentityContext(
        agent_id="test",
        role="test",
        core_directives=[],
        ethical_constraints=[],
        skills=["python"],
        knowledge_domains=["code"],
        tools_allowed=["search"],
        tools_forbidden=["delete"]
    )

    tags = SignalTags(
        domain="code",
        required_skills=["python"],
        required_tools=["search"],
        urgency_score=0.5,
        complexity_score=0.5
    )

    gap = await detect_capability_gap(tags, identity)
    assert gap is None

    tags2 = SignalTags(
        domain="finance",
        required_skills=["trading"],
        required_tools=["broker"],
        urgency_score=0.5,
        complexity_score=0.5
    )

    gap2 = await detect_capability_gap(tags2, identity)
    assert len(gap2.missing_knowledge) == 2
    assert len(gap2.missing_tools) == 1

    tags3 = SignalTags(domain="code", required_skills=[], required_tools=["delete"], urgency_score=0.5, complexity_score=0.5)
    gap3 = await detect_capability_gap(tags3, identity)
    assert gap3.constraint_violations == ["tool_forbidden:delete"]


@pytest.mark.asyncio
async def test_llm_fallback_capability_gap():
    kit = MagicMock(spec=InferenceKit)
    kit.has_llm = True

    mock_resp = MagicMock()
    mock_resp.content = '```json\n[]\n```'

    kit.llm = AsyncMock()
    kit.llm.complete.return_value = mock_resp
    kit.llm_config = MagicMock()

    identity = IdentityContext(
        agent_id="x", role="x", core_directives=[], ethical_constraints=[],
        skills=["python_expert"], knowledge_domains=["code"], tools_allowed=[], tools_forbidden=[]
    )

    tags = SignalTags(
        domain="code",
        required_skills=["basic_python"],
        required_tools=[],
        urgency_score=0.5, complexity_score=0.5
    )

    gap = await detect_capability_gap(tags, identity, kit=kit)
    assert gap is None


def test_update_cognitive_state():
    state1 = update_cognitive_state(agent_id="test1", processing_phase=ProcessingPhase.OBSERVE)
    assert state1.agent_id == "test1"
    assert state1.processing_phase == ProcessingPhase.OBSERVE

    state2 = get_current_state()
    assert state2.agent_id == "test1"


def test_accuracy_history(monkeypatch):
    class MockSettings:
        self_model_calibration_ema_decay: float = 0.1
        self_model_calibration_window: int = 10
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.self_model.engine.get_settings", lambda: MockKernelSettings())

    update_accuracy_history(1.0, 0.8, domain="test")
    hist = get_calibration_history()
    assert hist.sample_count > 0
    assert "test" in hist.domain_accuracy
