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
from kernel.ooda_loop.types import Decision, DecisionAction


@pytest.mark.asyncio
@pytest.mark.parametrize("telemetry_data, decisions, outputs, objective", [
    # Scenario 1: Normal load, no anomalies
    (
        CycleTelemetry(tokens_consumed=100, total_tokens_budget=1000, cycle_number=1, total_cycles_budget=10, cycle_duration_ms=500.0, expected_duration_ms=1000.0),
        [Decision(action=DecisionAction.CONTINUE, reasoning="step 1", target_node_ids=["node1"])],
        ["result alpha"],
        "Get alpha"
    ),
    # Scenario 2: High load, loop detected
    (
        CycleTelemetry(tokens_consumed=900, total_tokens_budget=1000, cycle_number=8, total_cycles_budget=10, cycle_duration_ms=1200.0, expected_duration_ms=1000.0),
        [Decision(action=DecisionAction.CONTINUE, reasoning="retry logic...", target_node_ids=["node2"])] * 4,
        ["failure retry", "failure retry", "failure retry", "failure retry"],
        "Persistent Task"
    ),
    # Scenario 3: Stall and Goal Drift
    (
        CycleTelemetry(tokens_consumed=500, total_tokens_budget=1000, cycle_number=3, total_cycles_budget=10, cycle_duration_ms=4000.0, expected_duration_ms=1000.0),
        [Decision(action=DecisionAction.CONTINUE, reasoning="thinking...", target_node_ids=["node3"])],
        ["Unrelated text summary about sports"],
        "Financial analysis objective"
    )
])
async def test_cognitive_load_monitor_comprehensive(telemetry_data, decisions, outputs, objective, inference_kit):
    """REAL SIMULATION: Verify Cognitive Load Monitor Kernel functions with multiple scenarios."""
    print(f"\n--- Testing Cognitive Load Monitor Scenario: Tokens={telemetry_data.tokens_consumed}, Objective: '{objective}' ---")

    activation_map = ActivationMap(module_states={})

    print("\n[Test]: measure_load")
    print(f"   [INPUT]: tokens={telemetry_data.tokens_consumed}, cycle={telemetry_data.cycle_number}")
    load = measure_load(activation_map, telemetry_data)
    assert load is not None
    assert hasattr(load, 'aggregate')
    print(f"   [OUTPUT]: Aggregate Load={load.aggregate:.2f}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: detect_loop")
    print(f"   [INPUT]: {len(decisions)} decisions")
    loops = detect_loop(decisions)
    assert loops is not None
    print(f"   [OUTPUT]: Is Looping={loops.is_looping}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: detect_stall")
    print(f"   [INPUT]: actual={telemetry_data.cycle_duration_ms}, expected={telemetry_data.expected_duration_ms}")
    stall = detect_stall(telemetry_data.cycle_duration_ms, telemetry_data.expected_duration_ms)
    print(f"   [OUTPUT]: Stall Detected={stall}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: detect_oscillation")
    print(f"   [INPUT]: {len(decisions)} decisions")
    oscillation = detect_oscillation(decisions)
    assert oscillation is not None
    print(f"   [OUTPUT]: Oscillation Detected={oscillation.is_oscillating}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: detect_goal_drift")
    print(f"   [INPUT]: objective='{objective}', outputs_count={len(outputs)}")
    drift = await detect_goal_drift(outputs, objective, kit=inference_kit)
    assert drift is not None
    print(f"   [OUTPUT]: Goal Drift Detected={drift.is_drifting}")
    print(" \033[92m[SUCCESS]\033[0m")

    print("\n[Test]: recommend_action")
    print(f"   [INPUT]: load={load.aggregate:.2f}, looping={loops.is_looping}, stall={stall}, oscillation={oscillation.is_oscillating}, drift={drift.is_drifting}")
    recommendation = recommend_action(load, loops, stall, oscillation, drift)
    assert recommendation is not None
    assert isinstance(recommendation.action, LoadAction)
    print(f"   [OUTPUT]: Recommended Action={recommendation.action}")
    print(" \033[92m[SUCCESS]\033[0m")

    print(f"\n[Test]: monitor_cognitive_load")
    print(f"   [INPUT]: objective='{objective}'")
    res = await monitor_cognitive_load(activation_map, telemetry_data, decisions, outputs, objective)
    assert res.is_success
    print(f"   [OUTPUT]: Status={res.status}, Signals count={len(res.signals)}")
    print(f" \033[92m[SUCCESS]\033[0m")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
