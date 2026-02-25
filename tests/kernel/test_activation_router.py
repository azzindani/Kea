import pytest

from kernel.activation_router.engine import (
    classify_signal,
    select_pipeline_template,
    adapt_to_pressure,
    cache_routing_decision,
    run_activation_router
)
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("input_text", [
    "Find the stock price of Apple.",
    "Draft a legal contract for a freelance developer",
    "Identify security vulnerabilities in the following code snippet",
    "Help",
    ""
])
async def test_activation_router_comprehensive(input_text):
    """REAL SIMULATION: Verify Activation Router Kernel functions with multiple inputs."""
    print(f"\n--- Testing Activation Router with Input: '{input_text}' ---")

    print(f"\n[Test]: classify_signal")
    classification = await classify_signal(input_text, kit=None)
    assert classification is not None
    assert hasattr(classification, 'complexity')
    print(f"   Complexity: {classification.complexity}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: select_pipeline_template")
    template = select_pipeline_template(classification)
    assert template is not None
    assert hasattr(template, 'template_id')
    print(f"   Template ID: {template.template_id}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: adapt_to_pressure")
    # Test with varying system pressure
    for pressure in [0.1, 0.5, 0.9]:
        adapted = adapt_to_pressure(template, pressure)
        assert adapted is not None
        assert len(adapted.active_modules) > 0
        print(f"   Pressure {pressure}: {len(adapted.active_modules)} active modules")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: cache_routing_decision")
    # Ensure it doesn't crash
    cache_routing_decision(input_text, template)
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: run_activation_router")
    res = await run_activation_router(input_text, kit=None)
    assert res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
