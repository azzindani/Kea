import pytest

from kernel.self_model.engine import (
    assess_capability,
    track_cognitive_state,
    detect_capability_gap,
    refresh_capability_map,
    update_accuracy_history,
    run_self_model
)
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("input_signal, target_domain", [
    ("Write a complex microservice in Python", "coding"),
    ("Perform an orbital calculation for a satellite", "science"),
    ("Analyze the market trends for coffee in Brazil", "finance"),
    ("Draft a formal apology letter", "general"),
    ("Fly a commercial airplane", "aviation")
])
async def test_self_model_comprehensive(input_signal, target_domain):
    """REAL SIMULATION: Verify Self Model Kernel functions with multiple capability scenarios."""
    print(f"\n--- Testing Self Model: Signal='{input_signal[:40]}...', Domain='{target_domain}' ---")

    print(f"\n[Test]: assess_capability")
    assessment = await assess_capability(input_signal, kit=None)
    assert assessment is not None
    assert hasattr(assessment, 'capability_score')
    print(f"   Capability Score for '{target_domain}': {assessment.capability_score:.2f}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: track_cognitive_state")
    cog_state = track_cognitive_state(assessment)
    assert cog_state is not None
    print(f"   Internal Load: {cog_state.current_load:.2f}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: detect_capability_gap")
    gap_result = detect_capability_gap(assessment)
    assert gap_result is not None
    print(f"   Gap Detected: {gap_result.is_gap_detected}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: update_accuracy_history")
    # Simulate a successful task completion in this domain
    update_accuracy_history(stated_confidence=0.9, actual_performance=1.0, domain=target_domain)
    print(f"   Outcome: Historian updated with performance data")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: refresh_capability_map")
    await refresh_capability_map()
    print(f"   Outcome: Capability map refreshed from central storage")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: run_self_model")
    res = await run_self_model(input_signal, kit=None)
    assert res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
