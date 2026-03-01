import pytest

from kernel.classification.engine import (
    run_linguistic_analysis,
    run_semantic_proximity,
    merge_classification_layers,
    classify
)
from kernel.classification.types import ClassProfileRules


@pytest.mark.asyncio
@pytest.mark.parametrize("text", [
    "Create a new file called main.py",
    "List all users in the system",
    "Deploy the production cluster now",
    "Help me with my homework",
    ""
])
async def test_classification_comprehensive(text, inference_kit):
    """REAL SIMULATION: Verify Classification Kernel functions with multiple inputs."""
    print(f"\n--- Testing Classification with Text: '{text}' ---")
    
    # Using an empty profile for pure engine testing (fallback behavior)
    profile = ClassProfileRules(pattern_rules=[], pos_rules=[], intent_vectors=[])

    print(f"\n[Test]: run_linguistic_analysis")
    print(f"   [INPUT]: '{text}'")
    linguistic_res = run_linguistic_analysis(text, profile)
    assert linguistic_res is not None
    print(f"   [OUTPUT]: Candidates count={len(linguistic_res.candidates)}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: run_semantic_proximity")
    print(f"   [INPUT]: '{text}'")
    semantic_res = await run_semantic_proximity(text, profile, kit=inference_kit)
    assert semantic_res is not None
    print(f"   [OUTPUT]: Embedding used={semantic_res.embedding_used}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: merge_classification_layers")
    print(f"   [INPUT]: Linguistic={len(linguistic_res.candidates)} candidates, Semantic proximity={semantic_res.embedding_used}")
    threshold = 0.5
    merged = merge_classification_layers(linguistic_res, semantic_res, threshold)
    assert merged is not None
    print(f"   [OUTPUT]: Result Type={type(merged).__name__}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: classify")
    print(f"   [INPUT]: '{text}'")
    res = await classify(text, profile, kit=inference_kit)
    assert res.is_success
    print(f"   [OUTPUT]: Status={res.status}, Signals count={len(res.signals)}")
    print(" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
