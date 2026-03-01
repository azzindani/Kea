from kernel.confidence_calibrator.types import CalibratedConfidence
from kernel.hallucination_monitor.types import GroundingReport
from kernel.noise_gate.engine import annotate_output, apply_quality_threshold
from kernel.noise_gate.types import ToolOutput


def test_apply_quality_threshold(monkeypatch):
    class MockSettings:
        noise_gate_grounding_threshold: float = 0.8
        noise_gate_confidence_threshold: float = 0.8
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.noise_gate.engine.get_settings", lambda: MockKernelSettings())

    assert apply_quality_threshold(0.9, 0.9)
    assert not apply_quality_threshold(0.5, 0.9)
    # override applies
    assert apply_quality_threshold(0.5, 0.9, quality_bar_override=0.4)

def test_annotate_output():
    out = ToolOutput(output_id="t1", tool_name="t", content="test")
    gr = GroundingReport(output_id="t1", total_claims=1, grounded_count=1, inferred_count=0, fabricated_count=0, claim_grades=[], grounding_score=0.9)
    conf = CalibratedConfidence(stated_confidence=0.9, calibrated_confidence=0.9, correction_factor=1.0, is_overconfident=False, is_underconfident=False, domain="g")

    filtered = annotate_output(out, gr, conf)
    assert filtered.passed
    assert filtered.quality.grounding_score == 0.9
