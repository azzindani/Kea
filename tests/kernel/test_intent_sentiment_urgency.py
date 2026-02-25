import pytest

from kernel.intent_sentiment_urgency.engine import (
    detect_intent,
    analyze_sentiment,
    score_urgency,
    run_primitive_scorers
)
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("text_input", [
    "HELP! The production database is unresponsive and data is being corrupted!",
    "Hi, could you please tell me how to change my password next week?",
    "This system is absolute garbage, I hate using this every single day.",
    "Excellent work on the latest update, the speed improvement is massive.",
    "Normal request to list files in /tmp directory."
])
async def test_intent_sentiment_urgency_comprehensive(text_input):
    """REAL SIMULATION: Verify Intent, Sentiment, & Urgency Kernel functions with multiple inputs."""
    print(f"\n--- Testing Intent, Sentiment & Urgency: Text='{text_input[:40]}...' ---")

    print(f"\n[Test]: detect_intent")
    intent_data = detect_intent(text_input)
    assert intent_data is not None
    # Assuming intent_data has 'intents' list which contains IntentLabel objects
    assert len(intent_data.intents) > 0
    print(f"   Primary Intent: {intent_data.intents[0].category.value}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: analyze_sentiment")
    sentiment_data = analyze_sentiment(text_input)
    assert sentiment_data is not None
    print(f"   Sentiment Score: {sentiment_data.score:.2f} (Label: {sentiment_data.category.value})")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: score_urgency")
    urgency_data = score_urgency(text_input)
    assert urgency_data is not None
    print(f"   Urgency Score: {urgency_data.score:.2f}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: run_primitive_scorers")
    res = await run_primitive_scorers(text_input, kit=None)
    assert res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
