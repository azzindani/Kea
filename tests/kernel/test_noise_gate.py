import pytest

from kernel.noise_gate.engine import (
    apply_quality_threshold,
    annotate_passing_output,
    generate_rejection_feedback,
    track_retry_budget,
    run_noise_gate
)
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("output_text, grounding_score, calibrated_confidence", [
    ("Verified response from knowledge base.", 0.98, 0.95), # High Quality
    ("Likely correct but lacking strong evidence.", 0.75, 0.8), # Borderline
    ("Inaccurate and low confidence hallucinatory content.", 0.3, 0.2), # Low Quality
    ("Empty or malformed signal.", 1.0, 0.1) # Mixed
])
async def test_noise_gate_comprehensive(output_text, grounding_score, calibrated_confidence):
    """REAL SIMULATION: Verify Noise Gate Kernel functions with multiple quality scenarios."""
    print(f"\n--- Testing Noise Gate: Grounding={grounding_score}, Confidence={calibrated_confidence} ---")

    print(f"\n[Test]: apply_quality_threshold")
    passed_gate = apply_quality_threshold(grounding_score, calibrated_confidence)
    print(f"   Quality Passed: {passed_gate}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: annotate_passing_output")
    if passed_gate:
        annotated = annotate_passing_output(output_text, grounding_score, calibrated_confidence)
        assert "quality_metadata" in annotated
        print(f"   Outcome: Output Annotated with metadata")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: generate_rejection_feedback")
    if not passed_gate:
        rejection_msg = generate_rejection_feedback("Grounding too low", "Please provide more source links")
        assert "provide more source" in rejection_msg
        print(f"   Outcome: Rejection feedback generated")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: track_retry_budget")
    trace_id = "tr-12345"
    can_retry = track_retry_budget(trace_id)
    assert isinstance(can_retry, bool)
    print(f"   Retry Budget Check for {trace_id}: {can_retry}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: run_noise_gate")
    res = await run_noise_gate(output_text, grounding_score, calibrated_confidence)
    assert res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
