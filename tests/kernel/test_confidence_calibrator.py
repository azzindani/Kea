import pytest

from kernel.confidence_calibrator.engine import (
    calibrate_confidence,
    detect_overconfidence,
    detect_underconfidence,
    update_calibration_curve,
    get_calibration_curve,
    run_confidence_calibration
)
from kernel.self_model.types import CalibrationHistory
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("stated_conf, grounding_score, domain", [
    (0.95, 0.98, "coding"),
    (0.95, 0.40, "general"),
    (0.30, 0.90, "finance"),
    (1.00, 0.05, "legal"),
    (0.50, 0.50, "medical")
])
async def test_confidence_calibrator_comprehensive(stated_conf, grounding_score, domain):
    """REAL SIMULATION: Verify Confidence Calibrator Kernel functions with multiple scenarios."""
    print(f"\n--- Testing Confidence Calibrator: Stated={stated_conf}, Grounding={grounding_score}, Domain={domain} ---")

    history = CalibrationHistory()

    print(f"\n[Test]: get_calibration_curve")
    curve = get_calibration_curve(domain)
    assert curve is not None
    assert curve.domain == domain
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: calibrate_confidence")
    calibrated_res = calibrate_confidence(stated_conf, grounding_score, history, domain=domain)
    assert calibrated_res is not None
    assert calibrated_res.calibrated_confidence <= grounding_score
    print(f"   Calibrated Confidence: {calibrated_res.calibrated_confidence}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: detect_overconfidence")
    overconf = detect_overconfidence(stated_conf, calibrated_res.calibrated_confidence)
    print(f"   Is Overconfident: {overconf}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: detect_underconfidence")
    underconf = detect_underconfidence(stated_conf, calibrated_res.calibrated_confidence)
    print(f"   Is Underconfident: {underconf}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: update_calibration_curve")
    update_calibration_curve(stated_conf, grounding_score, domain=domain)
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: run_confidence_calibration")
    res = await run_confidence_calibration(stated_conf, grounding_score, history, domain=domain)
    assert res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
