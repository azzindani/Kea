import pytest

from kernel.attention_and_plausibility.engine import (
    apply_attention_filter,
    check_plausibility,
    run_attention_and_plausibility
)
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("raw_input, conversation_history", [
    ("Find the stock price of Apple.", ["user previously asked about tech stocks"]),
    ("Draft a summary of the meeting we had earlier today.", ["meeting notes from 10am found", "user wants summary"]),
    ("kjashdkjashd kjahsdkjahsd", []),
    ("Tell me a joke about robots", ["system just rebooted"])
])
async def test_attention_and_plausibility_comprehensive(raw_input, conversation_history):
    """REAL SIMULATION: Verify Attention & Plausibility Kernel functions with multiple inputs."""
    print(f"\n--- Testing Attention & Plausibility with Input: '{raw_input}' ---")

    print(f"\n[Test]: apply_attention_filter")
    refined_state = apply_attention_filter(raw_input, conversation_history)
    assert refined_state is not None
    print(f"   Is Refined: {refined_state.is_refined}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: check_plausibility")
    plausibility_res = await check_plausibility(refined_state, kit=None)
    assert hasattr(plausibility_res, 'is_plausible')
    print(f"   Is Plausible: {plausibility_res.is_plausible}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: run_attention_and_plausibility")
    res = await run_attention_and_plausibility(raw_input, conversation_history, kit=None)
    assert res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
