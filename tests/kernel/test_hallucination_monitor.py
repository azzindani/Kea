import pytest

from kernel.hallucination_monitor.engine import (
    classify_claims,
    grade_claim,
    calculate_grounding_score,
    verify_grounding
)
from kernel.hallucination_monitor.types import Origin
from kernel.noise_gate.types import ToolOutput


@pytest.mark.asyncio
@pytest.mark.parametrize("source_text, evidence_context", [
    # Scenario 1: Factually correct
    (
        "Kea v0.4.0 is an Autonomous Enterprise Operating System.",
        "The latest documentation for Kea v0.4.0 describes it as an Autonomous Enterprise Operating System."
    ),
    # Scenario 2: Hallucination (Direct contradiction)
    (
        "The system is currently running on a quantum processor.",
        "The system status report shows it is running on standard x86_64 cloud instances."
    ),
    # Scenario 3: Unverifiable claim
    (
        "Users in Sector 7 are extremely happy with the performance.",
        "Performance logs for all sectors show stable latency, but no user sentiment data is available."
    ),
    # Scenario 4: Multiple claims
    (
        "Revenue increased by 10% and costs decreased by 5%.",
        "Financial records indicate a 10% growth in revenue but costs remained flat."
    )
])
async def test_hallucination_monitor_comprehensive(source_text, evidence_context, inference_kit):
    """REAL SIMULATION: Verify Hallucination Monitor Kernel functions with multiple scenarios."""
    print(f"\n--- Testing Hallucination Monitor: Text='{source_text[:30]}...' ---")

    evidence = [Origin(origin_id="ev1", content=evidence_context)]

    print("\n[Test]: classify_claims")
    print(f"   [INPUT]: text='{source_text[:30]}...'")
    claims_list = await classify_claims(source_text, kit=inference_kit)
    assert isinstance(claims_list, list)
    print(f"   [OUTPUT]: Claims found count={len(claims_list)}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: grade_claim")
    grades = []
    print(f"   [INPUT]: {len(claims_list)} claims, evidence count={len(evidence)}")
    for claim in claims_list:
        grade = await grade_claim(claim, evidence, kit=inference_kit)
        grades.append(grade)
        print(f"     - [OUTPUT]: Claim='{claim.text[:20]}...' -> Grade={grade.grade.value}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: calculate_grounding_score")
    print(f"   [INPUT]: {len(grades)} grades")
    score = calculate_grounding_score(grades)
    assert 0.0 <= score <= 1.0
    print(f"   [OUTPUT]: Overall Grounding Score={score:.2f}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: verify_grounding")
    output = ToolOutput(output_id="test-out", content=source_text)
    print(f"   [INPUT]: source_text='{source_text[:30]}...'")
    res = await verify_grounding(output, evidence, kit=inference_kit)
    assert res.is_success
    print(f"   [OUTPUT]: Status={res.status}, Signals count={len(res.signals)}")
    print(" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
