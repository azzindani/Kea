import pytest

from kernel.intent_sentiment_urgency.engine import (
    detect_intent,
    analyze_sentiment,
    score_urgency,
    run_primitive_scorers
)



@pytest.mark.asyncio
@pytest.mark.parametrize("text_input", [
    "HELP! The production database is unresponsive and data is being corrupted!",
    "Hi, could you please tell me how to change my password next week?",
    "This system is absolute garbage, I hate using this every single day.",
    "Excellent work on the latest update, the speed improvement is massive.",
    "Normal request to list files in /tmp directory."
])
async def test_intent_sentiment_urgency_comprehensive(text_input, inference_kit):
    """REAL SIMULATION: Verify Intent, Sentiment, & Urgency Kernel functions with multiple inputs."""
    print(f"\n--- Testing Intent, Sentiment & Urgency: Text='{text_input[:40]}...' ---")

    print("\n[Test]: detect_intent")
    print(f"   [INPUT]: text='{text_input[:40]}...'")
    intent_data = detect_intent(text_input)
    assert intent_data is not None
    assert intent_data.primary is not None
    print(f"   [OUTPUT]: Primary Intent={intent_data.primary.value}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: analyze_sentiment")
    print(f"   [INPUT]: text='{text_input[:40]}...'")
    sentiment_data = analyze_sentiment(text_input)
    assert sentiment_data is not None
    print(f"   [OUTPUT]: Sentiment Score={sentiment_data.score:.2f} (Label={sentiment_data.primary.value})")
    print(f" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: score_urgency")
    print(f"   [INPUT]: text='{text_input[:40]}...'")
    urgency_data = score_urgency(text_input)
    assert urgency_data is not None
    print(f"   [OUTPUT]: Urgency Score={urgency_data.score:.2f}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: run_primitive_scorers")
    print(f"   [INPUT]: text='{text_input[:40]}...'")
    res = await run_primitive_scorers(text_input, kit=inference_kit)
    assert res.is_success
    print(f"   [OUTPUT]: Status={res.status}, Signals count={len(res.signals)}")
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
