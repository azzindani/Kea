import pytest

from kernel.scoring.engine import (
    compute_semantic_similarity,
    compute_precision_score,
    evaluate_reward_compliance,
    aggregate_scores,
    score
)
from kernel.scoring.types import ScoringMetadata, Constraint


@pytest.mark.asyncio
@pytest.mark.parametrize("task_desc", [
    "Critical system recovery",
])
async def test_scoring_comprehensive(task_desc, inference_kit):
    """REAL SIMULATION: Verify Scoring Kernel functions."""
    print(f"\n--- Testing Scoring: Task='{task_desc}' ---")

    print("\n[Test]: compute_semantic_similarity")
    t1, t2 = "The quick brown fox", "Small brown fox"
    print(f"   [INPUT]: t1='{t1}', t2='{t2}'")
    sim_score = await compute_semantic_similarity(t1, t2, kit=inference_kit)
    assert 0.0 <= sim_score <= 1.0
    print(f"   [OUTPUT]: Similarity Score={sim_score:.2f}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: compute_precision_score")
    print(f"   [INPUT]: t1='{t1}', t2='{t2}'")
    prec_score = await compute_precision_score(t1, t2, kit=inference_kit)
    assert 0.0 <= prec_score <= 1.0
    print(f"   [OUTPUT]: Precision Score={prec_score:.2f}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: evaluate_reward_compliance")
    content = "The fox jumped"
    constraint_val = "fox"
    from kernel.scoring.types import ConstraintType
    print(f"   [INPUT]: content='{content}', constraint='{constraint_val}' (CONTAINS)")
    reward_score = evaluate_reward_compliance(content, [Constraint(constraint_type=ConstraintType.CONTAINS, value=constraint_val)])
    assert reward_score == 1.0
    print(f"   [OUTPUT]: Reward Compliance Score={reward_score:.2f}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: aggregate_scores")
    print(f"   [INPUT]: semantic=0.8, precision=0.9, reward=1.0")
    metadata = ScoringMetadata(user_role="admin", task_type="technical")
    final_score = aggregate_scores(semantic=0.8, precision=0.9, reward=1.0, metadata=metadata)
    assert isinstance(final_score, float)
    assert final_score > 0.8
    print(f"   [OUTPUT]: Aggregated Score={final_score:.2f}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: score")
    output_sample = "Sample output"
    query_sample = "Sample query"
    print(f"   [INPUT]: output='{output_sample}', query='{query_sample}'")
    res = await score(output_sample, query_sample, kit=inference_kit)
    assert res.is_success
    processed_score = res.signals[0].body["data"]["score"]
    assert processed_score >= 0.0
    print(f"   [OUTPUT]: Orchestrator Score={processed_score:.2f}")
    print(" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
