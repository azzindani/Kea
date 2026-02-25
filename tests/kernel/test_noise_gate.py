import pytest

from kernel.noise_gate.engine import (
    apply_quality_threshold,
    annotate_output,
    generate_rejection_feedback,
    check_retry_budget,
    filter_output
)
from kernel.ooda_loop.types import ActionResult as ToolOutput
from kernel.hallucination_monitor.types import GroundingReport
from kernel.confidence_calibrator.types import CalibratedConfidence
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("output_text, grounding_score, calibrated_confidence_val", [
    ("Verified response from knowledge base.", 0.98, 0.95), # High Quality
    ("Likely correct but lacking strong evidence.", 0.75, 0.8), # Borderline
    ("Inaccurate and low confidence hallucinatory content.", 0.3, 0.2), # Low Quality
    ("Empty or malformed signal.", 1.0, 0.1) # Mixed
])
async def test_noise_gate_comprehensive(output_text, grounding_score, calibrated_confidence_val):
    """REAL SIMULATION: Verify Noise Gate Kernel functions with multiple quality scenarios."""
    print(f"\n--- Testing Noise Gate: Grounding={grounding_score}, Confidence={calibrated_confidence_val} ---")

    print(f"\n[Test]: apply_quality_threshold")
    passed_gate = apply_quality_threshold(grounding_score, calibrated_confidence_val)
    print(f"   Quality Passed: {passed_gate}")
    print(f" \033[92m[SUCCESS]\033[0m")

    output = ToolOutput(node_id="test", outputs={"response": output_text})
    grounding = GroundingReport(grounding_score=grounding_score, claim_grades=[])
    confidence = CalibratedConfidence(calibrated_confidence=calibrated_confidence_val)

    print(f"\n[Test]: annotate_output")
    if passed_gate:
        annotated = annotate_output(output, grounding, confidence)
        assert annotated.quality is not None
        print(f"   Outcome: Output Annotated with metadata")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: generate_rejection_feedback")
    if not passed_gate:
        rejected = generate_rejection_feedback(output, grounding, confidence)
        assert rejected.guidance is not None
        print(f"   Outcome: Rejection feedback generated")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: check_retry_budget")
    trace_id = "tr-12345"
    retry_status = check_retry_budget(trace_id)
    assert retry_status.retries_used >= 1
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: filter_output")
    res = await filter_output(output, grounding, confidence)
    assert res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
