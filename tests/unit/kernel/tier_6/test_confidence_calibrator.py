from kernel.confidence_calibrator.engine import calibrate_confidence
from kernel.self_model.types import CalibrationHistory


def test_calibrate_confidence(monkeypatch):
    # Mock get_calibration_curve
    from kernel.self_model.types import CalibrationCurve
    mock_curve = CalibrationCurve(domain="general", bin_mapping={"0.0": 0.0, "1.0": 1.0})
    monkeypatch.setattr("kernel.confidence_calibrator.engine.get_calibration_curve", lambda d: mock_curve)

    hist = CalibrationHistory()

    res = calibrate_confidence(stated_confidence=0.9, grounding_score=0.5, history=hist)

    assert res.stated_confidence == 0.9
    assert res.calibrated_confidence == 0.5 # Bounded by grounding
    assert res.is_overconfident
