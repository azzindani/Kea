import pytest

from kernel.classification.engine import (
    run_linguistic_analysis,
    run_semantic_proximity,
    merge_classification_layers,
    classify
)
from kernel.classification.types import ClassProfileRules
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("text", [
    "Create a new file called main.py",
    "List all users in the system",
    "Deploy the production cluster now",
    "Help me with my homework",
    ""
])
async def test_classification_comprehensive(text):
    """REAL SIMULATION: Verify Classification Kernel functions with multiple inputs."""
    print(f"\n--- Testing Classification with Text: '{text}' ---")
    
    # Using an empty profile for pure engine testing (fallback behavior)
    profile = ClassProfileRules(pattern_rules=[], pos_rules=[], intent_vectors=[])

    print(f"\n[Test]: run_linguistic_analysis")
    linguistic_res = run_linguistic_analysis(text, profile)
    assert linguistic_res is not None
    print(f"   Candidates count: {len(linguistic_res.candidates)}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: run_semantic_proximity")
    semantic_res = await run_semantic_proximity(text, profile)
    assert semantic_res is not None
    print(f"   Embedding used: {semantic_res.embedding_used}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: merge_classification_layers")
    threshold = 0.5
    merged = merge_classification_layers(linguistic_res, semantic_res, threshold)
    assert merged is not None
    print(f"   Result Type: {type(merged).__name__}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: classify")
    res = await classify(text, profile, kit=None)
    assert res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
