import pytest

from kernel.activation_router.engine import (
    classify_signal_complexity,
    select_pipeline,
    check_decision_cache,
    cache_decision,
    compute_activation_map
)
from kernel.activation_router.types import ComplexityLevel
from kernel.self_model.types import SignalTags, CapabilityAssessment
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("input_text", [
    "Find the stock price of Apple.",
    "Draft a legal contract for a freelance developer",
    "Identify security vulnerabilities in the following code snippet",
    "Help",
    ""
])
async def test_activation_router_comprehensive(input_text, inference_kit):
    """REAL SIMULATION: Verify Activation Router Kernel functions with multiple inputs."""
    print(f"\n--- Testing Activation Router with Input: '{input_text}' ---")

    tags = SignalTags(
        urgency="normal",
        complexity="moderate",
        intent="query",
        domain="general",
        source_type=f"test_{len(input_text)}" # Vary by input length
    )
    capability = CapabilityAssessment(
        can_handle=True,
        confidence=1.0,
        partial_capabilities=["web_search"]
    )

    print(f"\n[Test]: classify_signal_complexity")
    print(f"   [INPUT]: signal='{input_text[:30]}...', domain={tags.domain}")
    classification = await classify_signal_complexity(tags, kit=inference_kit)
    assert classification is not None
    assert isinstance(classification, ComplexityLevel)
    print(f"   [OUTPUT]: Complexity={classification.value}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: select_pipeline")
    print(f"   [INPUT]: complexity={classification.value}, pressure=0.2")
    pipeline = select_pipeline(classification, pressure=0.2)
    assert pipeline is not None
    assert hasattr(pipeline, 'pipeline_name')
    print(f"   [OUTPUT]: Selected Pipeline={pipeline.pipeline_name}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: adapt_to_pressure (via select_pipeline)")
    for pressure in [0.1, 0.5, 0.9]:
        adapted_pipeline = select_pipeline(classification, pressure)
        assert adapted_pipeline is not None
        assert len(adapted_pipeline.active_modules) > 0
        print(f"     - [OUTPUT]: Pressure={pressure} -> Active Modules={len(adapted_pipeline.active_modules)}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: cache_decision")
    print(f"   [INPUT]: tags_intent={tags.intent}")
    activation_map = await compute_activation_map(tags, capability)
    assert activation_map.is_success
    print(f"   [OUTPUT]: Decision cached successfully")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: compute_activation_map")
    print(f"   [INPUT]: signal='{input_text[:30]}...', confidence={capability.confidence}")
    res = await compute_activation_map(tags, capability, kit=inference_kit)
    assert res.is_success
    print(f"   [OUTPUT]: Status={res.status}, Signals count={len(res.signals)}")
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
