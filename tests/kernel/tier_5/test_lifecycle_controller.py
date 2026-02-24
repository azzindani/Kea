import pytest

from kernel.lifecycle_controller.engine import (
    initialize_agent,
    load_cognitive_profile,
    set_identity_constraints,
)
from kernel.lifecycle_controller.types import CognitiveProfile, SpawnRequest


@pytest.mark.asyncio
async def test_initialize_agent():
    req = SpawnRequest(role="tester", profile_id="p1")
    identity = await initialize_agent(req)
    assert identity.role == "tester"
    assert identity.profile_id == "p1"

@pytest.mark.asyncio
async def test_load_cognitive_profile(monkeypatch):
    class MockSettings:
        noise_gate_grounding_threshold: float = 0.8
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.lifecycle_controller.engine.get_settings", lambda: MockKernelSettings())

    prof = await load_cognitive_profile("p1")
    assert prof.profile_id == "p1"
    assert prof.quality_bar == 0.8

def test_set_identity_constraints():
    prof = CognitiveProfile(profile_id="p", role_name="r", skills=["python"], knowledge_domains=[], quality_bar=0.5)
    ctx = set_identity_constraints("a1", prof)
    assert ctx.agent_id == "a1"
    assert ctx.role == "r"
    assert "python" in ctx.skills
