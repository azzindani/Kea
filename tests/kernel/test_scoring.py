import pytest

from kernel.scoring.engine import (
    compute_semantic_similarity,
    compute_precision_score,
    evaluate_reward_compliance,
    aggregate_scores,
    score
)
from kernel.scoring.types import NumericScore, ScoringMetadata, Constraint


@pytest.mark.asyncio
@pytest.mark.parametrize("task_desc", [
    "Critical system recovery",
])
async def test_scoring_comprehensive(task_desc):
    """REAL SIMULATION: Verify Scoring Kernel functions."""
    print(f"\n--- Testing Scoring: Task='{task_desc}' ---")

    print("\n[Test]: compute_semantic_similarity")
    sim_score = await compute_semantic_similarity("The quick brown fox", "Small brown fox")
    assert 0.0 <= sim_score <= 1.0
    print(f"   Similarity Score: {sim_score:.2f}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: compute_precision_score")
    prec_score = await compute_precision_score("The quick brown fox", "Small brown fox")
    assert 0.0 <= prec_score <= 1.0
    print(f"   Precision Score: {prec_score:.2f}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: evaluate_reward_compliance")
    reward_score = evaluate_reward_compliance("The fox jumped", [Constraint(id="c1", rule="must contain fox")])
    assert reward_score == 1.0
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: aggregate_scores")
    metadata = ScoringMetadata(user_role="admin", task_type="technical")
    final_score = aggregate_scores(semantic=0.8, precision=0.9, reward=1.0, metadata=metadata)
    assert isinstance(final_score, NumericScore)
    assert final_score.score > 0.8
    print(f"   Aggregated Score: {final_score.score:.2f}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: score")
    res = await score("Sample output", "Sample query")
    assert res.score >= 0.0
    print(" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
