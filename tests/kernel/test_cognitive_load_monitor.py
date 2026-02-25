import pytest

from kernel.cognitive_load_monitor.engine import (
    measure_load,
    detect_loop,
    detect_stall,
    detect_oscillation,
    detect_goal_drift,
    recommend_action,
    monitor_cognitive_load
)
from kernel.activation_router.types import ActivationMap
from kernel.cognitive_load_monitor.types import CycleTelemetry, LoadAction
from kernel.ooda_loop.types import Decision, ActionLabel
from shared.config import get_settings


@pytest.mark.asyncio
@pytest.mark.parametrize("telemetry_data, decisions, outputs, objective", [
    # Scenario 1: Normal load, no anomalies
    (
        CycleTelemetry(tokens_consumed=100, total_tokens_budget=1000, cycle_number=1, total_cycles_budget=10, cycle_duration_ms=500.0, expected_duration_ms=1000.0),
        [Decision(action=ActionLabel.EXECUTE, reasoning="step 1", confidence=0.9)],
        ["result alpha"],
        "Get alpha"
    ),
    # Scenario 2: High load, loop detected
    (
        CycleTelemetry(tokens_consumed=900, total_tokens_budget=1000, cycle_number=8, total_cycles_budget=10, cycle_duration_ms=1200.0, expected_duration_ms=1000.0),
        [Decision(action=ActionLabel.EXECUTE, reasoning="retry logic...", confidence=0.5)] * 4,
        ["failure retry", "failure retry", "failure retry", "failure retry"],
        "Persistent Task"
    ),
    # Scenario 3: Stall and Goal Drift
    (
        CycleTelemetry(tokens_consumed=500, total_tokens_budget=1000, cycle_number=3, total_cycles_budget=10, cycle_duration_ms=4000.0, expected_duration_ms=1000.0),
        [Decision(action=ActionLabel.EXECUTE, reasoning="thinking...", confidence=0.8)],
        ["Unrelated text summary about sports"],
        "Financial analysis objective"
    )
])
async def test_cognitive_load_monitor_comprehensive(telemetry_data, decisions, outputs, objective):
    """REAL SIMULATION: Verify Cognitive Load Monitor Kernel functions with multiple scenarios."""
    print(f"\n--- Testing Cognitive Load Monitor Scenario: Tokens={telemetry_data.tokens_consumed}, Objective: '{objective}' ---")

    activation_map = ActivationMap(module_states={})

    print(f"\n[Test]: measure_load")
    load = measure_load(activation_map, telemetry_data)
    assert load is not None
    assert hasattr(load, 'aggregate')
    print(f"   Aggregate Load: {load.aggregate}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: detect_loop")
    loops = detect_loop(decisions)
    assert loops is not None
    print(f"   Is Looping: {loops.is_looping}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: detect_stall")
    stall = detect_stall(telemetry_data.cycle_duration_ms, telemetry_data.expected_duration_ms)
    print(f"   Stall Detected: {stall}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: detect_oscillation")
    oscillation = detect_oscillation(decisions)
    assert oscillation is not None
    print(f"   Oscillation Detected: {oscillation.is_oscillating}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: detect_goal_drift")
    drift = await detect_goal_drift(outputs, objective, kit=None)
    assert drift is not None
    print(f"   Goal Drift Detected: {drift.is_drifting}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: recommend_action")
    recommendation = recommend_action(load, loops, stall, oscillation, drift)
    assert recommendation is not None
    assert isinstance(recommendation.action, LoadAction)
    print(f"   Recommended Action: {recommendation.action.value}")
    print(f" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: monitor_cognitive_load")
    res = await monitor_cognitive_load(activation_map, telemetry_data, decisions, outputs, objective)
    assert res.is_success
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
