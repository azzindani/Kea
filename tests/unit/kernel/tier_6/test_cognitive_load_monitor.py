from unittest.mock import AsyncMock, MagicMock

import pytest

from kernel.activation_router.types import ActivationMap, ModuleState
from kernel.cognitive_load_monitor.engine import (
    detect_goal_drift,
    detect_loop,
    detect_oscillation,
    measure_load,
)
from kernel.cognitive_load_monitor.types import (
    CycleTelemetry,
)
from kernel.ooda_loop.types import Decision, DecisionAction
from shared.inference_kit import InferenceKit


def test_measure_load(monkeypatch):
    class MockSettings:
        load_compute_weight: float = 0.5
        load_time_weight: float = 0.3
        load_breadth_weight: float = 0.2
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.cognitive_load_monitor.engine.get_settings", lambda: MockKernelSettings())

    amap = ActivationMap(module_states={"mod1": ModuleState(value="active", confidence=1.0, required_capabilities=[])}, required_tools=[])
    telemetry = CycleTelemetry(
        cycle_number=10, total_cycles_budget=100,
        tokens_consumed=5000, total_tokens_budget=10000,
        cycle_duration_ms=1000.0, expected_duration_ms=800.0,
        active_module_count=1
    )

    load = measure_load(amap, telemetry)
    assert load.compute_load == 0.5
    assert load.time_load == 1.0
    assert load.breadth_load == 0.5
    assert load.aggregate == 0.65


def test_detect_loop(monkeypatch):
    class MockSettings:
        load_loop_detection_window: int = 10
        load_loop_repeat_threshold: int = 3
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.cognitive_load_monitor.engine.get_settings", lambda: MockKernelSettings())

    d1 = Decision(action=DecisionAction.CONTINUE, reasoning="R1")
    decisions = [d1, d1, d1]

    loop = detect_loop(decisions)
    assert loop.is_looping
    assert loop.loop_count >= 3
    assert loop.loop_length == 1


def test_detect_oscillation():
    d1 = Decision(action=DecisionAction.CONTINUE, reasoning="R1")
    d2 = Decision(action=DecisionAction.CONTINUE, reasoning="R2")

    osc = detect_oscillation([d1, d2, d1, d2])
    assert osc.is_oscillating
    assert osc.period == 2


@pytest.mark.asyncio
async def test_detect_goal_drift(monkeypatch):
    class MockSettings:
        load_goal_drift_threshold: float = 0.5
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.cognitive_load_monitor.engine.get_settings", lambda: MockKernelSettings())

    obj = "Build a red house"
    recent = ["I am building a red house and laying bricks", "I am painting the house red"]

    drift = await detect_goal_drift(recent, obj)
    assert not drift.is_drifting

    drift2 = await detect_goal_drift(["Some totally unrelated text about cars"], obj)
    assert drift2.is_drifting


@pytest.mark.asyncio
async def test_llm_fallback_detect_goal_drift(monkeypatch):
    class MockSettings:
        load_goal_drift_threshold: float = 0.5
    class MockKernelSettings:
        kernel = MockSettings()
    monkeypatch.setattr("kernel.cognitive_load_monitor.engine.get_settings", lambda: MockKernelSettings())

    kit = MagicMock(spec=InferenceKit)
    kit.has_embedder = True
    kit.embedder = AsyncMock()
    kit.embedder.embed.side_effect = lambda text: [1.0, 0.0] if "goal" in str(text) else [0.0, 1.0]

    drift = await detect_goal_drift(["unrelated output"], "goal objective", kit=kit)
    assert drift.is_drifting
    assert drift.drift_magnitude == 1.0
