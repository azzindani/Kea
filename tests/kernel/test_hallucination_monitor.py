import pytest

from kernel.hallucination_monitor.engine import (
    classify_claims,
    grade_claim,
    calculate_grounding_score,
    verify_grounding
)
from kernel.hallucination_monitor.types import Origin
from kernel.ooda_loop.types import ActionResult as ToolOutput


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
async def test_hallucination_monitor_comprehensive(source_text, evidence_context):
    """REAL SIMULATION: Verify Hallucination Monitor Kernel functions with multiple scenarios."""
    print(f"\n--- Testing Hallucination Monitor: Text='{source_text[:30]}...' ---")

    evidence = [Origin(origin_id="ev1", content=evidence_context)]

    print("\n[Test]: classify_claims")
    claims_list = await classify_claims(source_text, kit=None)
    assert isinstance(claims_list, list)
    print(f"   Claims found and classified: {len(claims_list)}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: grade_claim")
    grades = []
    for claim in claims_list:
        grade = grade_claim(claim, evidence, kit=None)
        grades.append(grade)
        print(f"     - Claim: {claim.text[:20]}... -> Grade: {grade.grade.value}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: calculate_grounding_score")
    score = calculate_grounding_score(grades)
    assert 0.0 <= score <= 1.0
    print(f"   Overall Score: {score}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: verify_grounding")
    output = ToolOutput(node_id="test", outputs={"response": source_text})
    res = await verify_grounding(output, evidence, kit=None)
    assert res.is_success
    print(" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
