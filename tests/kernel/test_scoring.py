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
    "Enterprise Cloud Cost Optimization Report",
    "Security Vulnerability Patch Analysis",
])
async def test_scoring_comprehensive(task_desc, inference_kit):
    """REAL SIMULATION: Verify Scoring Kernel functions with enterprise-grade payloads."""
    print(f"\n--- Testing Scoring: Task='{task_desc}' ---")

    print("\n[Test]: compute_semantic_similarity")
    t1 = '{"status": "success", "data": {"nodes": 12, "cost_saving": "$12k"}, "metadata": {"region": "us-east-1"}}'
    t2 = '{"outcome": "completed", "savings": "12000 USD", "cluster_size": 12}'
    print(f"   [INPUT]: t1='{t1[:50]}...', t2='{t2[:50]}...'")
    sim_score = await compute_semantic_similarity(t1, t2, kit=inference_kit)
    assert 0.0 <= sim_score <= 1.0
    print(f"   [OUTPUT]: Semantic Alignment={sim_score:.2f}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: compute_precision_score")
    expected_fidelity = "The report must include exact cost reductions and affected cluster IDs."
    actual_output = "The optimization saved 12% across clusters IDs: [k8s-01, k8s-05, k8s-12]."
    print(f"   [INPUT]: expected='{expected_fidelity}', actual='{actual_output}'")
    prec_score = await compute_precision_score(expected_fidelity, actual_output, kit=inference_kit)
    assert 0.0 <= prec_score <= 1.0
    print(f"   [OUTPUT]: Technical Precision={prec_score:.2f}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: evaluate_reward_compliance")
    content = '{"patch_status": "applied", "reboot_required": false}'
    # Constraint: Must contain 'applied'
    from kernel.scoring.types import ConstraintType
    constraint_val = "applied"
    print(f"   [INPUT]: content='{content}', constraint='{constraint_val}' (CONTAINS)")
    reward_score = evaluate_reward_compliance(content, [Constraint(constraint_type=ConstraintType.CONTAINS, value=constraint_val)])
    assert reward_score == 1.0
    print(f"   [OUTPUT]: Policy Compliance={reward_score:.2f}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: aggregate_scores")
    print(f"   [INPUT]: semantic=0.85, precision=0.92, reward=1.0")
    metadata = ScoringMetadata(user_role="principal_architect", task_type="infrastructure_governance")
    final_score = aggregate_scores(semantic=0.85, precision=0.92, reward=1.0, metadata=metadata)
    assert final_score > 0.9
    print(f"   [OUTPUT]: Final Quality Score={final_score:.2f} (Weights applied)")
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
