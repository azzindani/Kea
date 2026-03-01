import pytest

from kernel.attention_and_plausibility.engine import (
    filter_attention,
    check_plausibility,
    run_cognitive_filters
)
from kernel.attention_and_plausibility.types import TaskState, ContextElement


@pytest.mark.asyncio
@pytest.mark.parametrize("raw_input, conversation_history", [
    ("Find the stock price of Apple.", ["user previously asked about tech stocks"]),
    ("Draft a summary of the meeting we had earlier today.", ["meeting notes from 10am found", "user wants summary"]),
    ("kjashdkjashd kjahsdkjahsd", []),
    ("Tell me a joke about robots", ["system just rebooted"])
])
async def test_attention_and_plausibility_comprehensive(raw_input, conversation_history, inference_kit):
    """REAL SIMULATION: Verify Attention & Plausibility Kernel functions with multiple inputs."""
    print(f"\n--- Testing Attention & Plausibility with Input: '{raw_input}' ---")

    task_state = TaskState(
        goal=raw_input,
        context_elements=[ContextElement(key=f"hist_{i}", value=val) for i, val in enumerate(conversation_history)]
    )

    print("\n[Test]: filter_attention")
    print(f"   [INPUT]: goal='{raw_input}', context_elements={len(task_state.context_elements)}")
    filtered_state = await filter_attention(task_state)
    assert filtered_state is not None
    print(f"   [OUTPUT]: Dropped Count={filtered_state.dropped_count}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: check_plausibility")
    print(f"   [INPUT]: goal='{filtered_state.goal}'")
    plausibility_res = await check_plausibility(filtered_state, kit=inference_kit)
    assert hasattr(plausibility_res, 'verdict')
    print(f"   [OUTPUT]: Verdict={plausibility_res.verdict}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: run_cognitive_filters")
    print(f"   [INPUT]: goal='{raw_input}'")
    res = await run_cognitive_filters(task_state, kit=inference_kit)
    assert res.is_success
    print(f"   [OUTPUT]: Status={res.status}, Signals count={len(res.signals)}")
    print(" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
