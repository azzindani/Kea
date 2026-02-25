import pytest

from kernel.hallucination_monitor.engine import (
    extract_claims,
    classify_claims,
    grade_claims,
    run_hallucination_monitor
)
from shared.config import get_settings


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

    print(f"\n[Test]: extract_claims")
    claims_list = await extract_claims(source_text, kit=None)
    assert isinstance(claims_list, list)
    print(f"   Claims found: {len(claims_list)}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: classify_claims")
    classified_claims = classify_claims(claims_list)
    assert len(classified_claims) == len(claims_list)
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: grade_claims")
    graded_claims = await grade_claims(classified_claims, evidence_context, kit=None)
    assert len(graded_claims) == len(claims_list)
    for gc in graded_claims:
        print(f"     - Claim: {gc.claim_text[:20]}... -> Grade: {gc.grounding_grade.value}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: run_hallucination_monitor")
    res = await run_hallucination_monitor(source_text, evidence_context, kit=None)
    assert res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
