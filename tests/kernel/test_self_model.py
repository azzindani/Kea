import pytest

from kernel.self_model.engine import (
    assess_capability,
    update_cognitive_state,
    detect_capability_gap,
    update_accuracy_history,
    refresh_capability_map,
    run_self_model
)
from kernel.self_model.types import SignalTags
from kernel.lifecycle_controller.types import IdentityContext
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("input_signal, target_domain", [
    ("Write a complex microservice in Python", "coding"),
    ("Perform an orbital calculation for a satellite", "science"),
])
async def test_self_model_comprehensive(input_signal, target_domain):
    """REAL SIMULATION: Verify Self Model Kernel functions."""
    print(f"\n--- Testing Self Model: Signal='{input_signal[:40]}...', Domain='{target_domain}' ---")

    tags = SignalTags(urgency="normal", complexity="moderate", intent="query", domain=target_domain)
    identity = IdentityContext(
        agent_id="test_agent", 
        role="security_auditor", 
        skills=frozenset(["coding"]),
        tools_allowed=frozenset(["bash"]),
        tools_forbidden=frozenset([]),
        knowledge_domains=frozenset(["security"]),
        ethical_constraints=(),
        quality_bar=0.7
    )

    print(f"\n[Test]: assess_capability")
    assessment = await assess_capability(tags, identity, kit=None)
    assert assessment is not None
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: update_cognitive_state")
    from kernel.self_model.types import ProcessingPhase
    update_cognitive_state(agent_id="test_agent", processing_phase=ProcessingPhase.IDLE)
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: detect_capability_gap")
    gap = await detect_capability_gap(tags, identity, kit=None)
    if gap:
        print(f"   Gap Detected: {gap.missing_knowledge}")
    else:
        print("   No gap detected")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: update_accuracy_history")
    update_accuracy_history(predicted=0.9, actual=1.0, domain=target_domain)
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: refresh_capability_map")
    await refresh_capability_map(identity=identity)
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: run_self_model")
    res = await run_self_model(tags, identity, kit=None)
    assert res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
