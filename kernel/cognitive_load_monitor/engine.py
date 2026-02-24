"""
Tier 6 Cognitive Load Monitor — Engine.

Processing budget measurement and anomaly detection:
    1. Measure three-dimensional cognitive load (compute, time, breadth)
    2. Detect repetitive decision loops (strict + fuzzy matching)
    3. Detect stalls (cycle duration exceeding threshold)
    4. Detect oscillation (A→B→A→B alternating patterns)
    5. Detect goal drift (semantic divergence from objective)
    6. Recommend graduated response action
"""

from __future__ import annotations

import hashlib
import time

import numpy as np

from kernel.activation_router.types import ActivationMap
from kernel.ooda_loop.types import Decision
from shared.config import get_settings
from shared.inference_kit import InferenceKit
from shared.logging.main import get_logger
from shared.standard_io import (
    Metrics,
    ModuleRef,
    Result,
    create_data_signal,
    fail,
    ok,
    processing_error,
)

from .types import (
    CognitiveLoad,
    CycleTelemetry,
    GoalDriftDetection,
    LoadAction,
    LoadRecommendation,
    LoopDetection,
    OscillationDetection,
)

log = get_logger(__name__)

_MODULE = "cognitive_load_monitor"
_TIER = 6


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


def _decision_hash(decision: Decision) -> str:
    """Generate a hash fingerprint for a decision."""
    raw = f"{decision.action.value}|{decision.reasoning}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


# ============================================================================
# Step 1: Measure Load
# ============================================================================


def measure_load(
    activation_map: ActivationMap,
    telemetry: CycleTelemetry,
) -> CognitiveLoad:
    """Compute the current cognitive load across three dimensions.

    Compute: tokens + cycles vs budget.
    Time: wall clock vs expected duration.
    Breadth: active modules vs hardware capacity.
    """
    settings = get_settings().kernel

    # Compute dimension: tokens + cycles consumed vs budget
    token_ratio = (
        telemetry.tokens_consumed / telemetry.total_tokens_budget
        if telemetry.total_tokens_budget > 0
        else 0.0
    )
    cycle_ratio = (
        telemetry.cycle_number / telemetry.total_cycles_budget
        if telemetry.total_cycles_budget > 0
        else 0.0
    )
    compute_load = min(1.0, max(token_ratio, cycle_ratio))

    # Time dimension: wall clock vs expected
    time_load = 0.0
    if telemetry.expected_duration_ms > 0:
        time_load = min(
            1.0,
            telemetry.cycle_duration_ms / telemetry.expected_duration_ms,
        )

    # Breadth dimension: active modules vs capacity
    active_count = len([
        v for v in activation_map.module_states.values()
        if v.value == "active"
    ])
    max_modules = max(1, telemetry.active_module_count or active_count)
    breadth_load = min(1.0, active_count / max(1, max_modules * 2))

    # Weighted aggregate
    aggregate = (
        settings.load_compute_weight * compute_load
        + settings.load_time_weight * time_load
        + settings.load_breadth_weight * breadth_load
    )

    return CognitiveLoad(
        compute_load=round(compute_load, 4),
        time_load=round(time_load, 4),
        breadth_load=round(breadth_load, 4),
        aggregate=round(min(1.0, aggregate), 4),
    )


# ============================================================================
# Step 2: Detect Loop
# ============================================================================


def detect_loop(recent_decisions: list[Decision]) -> LoopDetection:
    """Analyze recent decisions for repetitive patterns.

    Uses decision hash comparison to detect exact and near-loops.
    """
    settings = get_settings().kernel
    window = settings.load_loop_detection_window
    repeat_threshold = settings.load_loop_repeat_threshold

    # Take only the latest N decisions
    windowed = recent_decisions[-window:] if len(recent_decisions) > window else recent_decisions

    if len(windowed) < repeat_threshold:
        return LoopDetection()

    hashes = [_decision_hash(d) for d in windowed]

    # Check for exact repetition (same decision N times in a row)
    for length in range(1, len(hashes) // repeat_threshold + 1):
        pattern = hashes[-length:]
        match_count = 0
        for i in range(len(hashes) - length, -1, -length):
            segment = hashes[i:i + length]
            if segment == pattern:
                match_count += 1
            else:
                break

        if match_count >= repeat_threshold:
            repeated_descriptions = [
                windowed[-(j + 1)].reasoning
                for j in range(length)
            ]
            return LoopDetection(
                is_looping=True,
                loop_length=length,
                loop_count=match_count,
                repeated_pattern=repeated_descriptions,
            )

    return LoopDetection()


# ============================================================================
# Step 3: Detect Stall
# ============================================================================


def detect_stall(
    cycle_duration: float,
    expected_duration: float,
) -> bool:
    """Check if the current cycle is stalled.

    Returns True if cycle_duration > expected_duration * stall_multiplier.
    """
    settings = get_settings().kernel
    multiplier = settings.load_stall_multiplier

    if expected_duration <= 0:
        return False

    return cycle_duration > (expected_duration * multiplier)


# ============================================================================
# Step 4: Detect Oscillation
# ============================================================================


def detect_oscillation(recent_decisions: list[Decision]) -> OscillationDetection:
    """Detect alternating A→B→A→B or A→B→C→A→B→C patterns.

    Uses autocorrelation on decision hash sequences.
    """
    if len(recent_decisions) < 4:
        return OscillationDetection()

    hashes = [_decision_hash(d) for d in recent_decisions]

    # Check period-2 oscillation (A, B, A, B)
    if len(hashes) >= 4:
        is_period_2 = True
        for i in range(len(hashes) - 2):
            if hashes[i] != hashes[i + 2]:
                is_period_2 = False
                break

        if is_period_2 and hashes[-1] != hashes[-2]:
            return OscillationDetection(
                is_oscillating=True,
                period=2,
                conflicting_decisions=[
                    recent_decisions[-2].reasoning,
                    recent_decisions[-1].reasoning,
                ],
            )

    # Check period-3 oscillation (A, B, C, A, B, C)
    if len(hashes) >= 6:
        is_period_3 = True
        for i in range(len(hashes) - 3):
            if hashes[i] != hashes[i + 3]:
                is_period_3 = False
                break

        if is_period_3:
            return OscillationDetection(
                is_oscillating=True,
                period=3,
                conflicting_decisions=[
                    recent_decisions[-3].reasoning,
                    recent_decisions[-2].reasoning,
                    recent_decisions[-1].reasoning,
                ],
            )

    return OscillationDetection()


# ============================================================================
# Step 5: Detect Goal Drift
# ============================================================================


async def detect_goal_drift(
    recent_outputs: list[str],
    original_objective: str,
    kit: InferenceKit | None = None,
) -> GoalDriftDetection:
    """Compute semantic similarity between recent outputs and the objective.

    If the rolling average similarity drops below threshold, flags drift.
    Uses a simple keyword overlap heuristic at the kernel level;
    the service layer can inject embedding-based similarity.
    """
    settings = get_settings().kernel
    drift_threshold = settings.load_goal_drift_threshold

    if not recent_outputs or not original_objective:
        return GoalDriftDetection()

    if kit and kit.has_embedder:
        try:
            obj_emb = await kit.embedder.embed(original_objective)
            similarities = []
            for out in recent_outputs:
                out_emb = await kit.embedder.embed(out)
                score = np.dot(obj_emb, out_emb) / (np.linalg.norm(obj_emb) * np.linalg.norm(out_emb))
                similarities.append(round(float(score), 4))

            avg_similarity = sum(similarities) / max(1, len(similarities))
            is_drifting = avg_similarity < drift_threshold
            drift_magnitude = max(0.0, 1.0 - avg_similarity)

            return GoalDriftDetection(
                is_drifting=is_drifting,
                similarity_trend=similarities,
                drift_magnitude=round(drift_magnitude, 4),
            )
        except Exception as e:
            log.warning("Embedding goal drift failed, falling back", error=str(e))
            pass

    # Kernel-level heuristic: keyword overlap as similarity proxy.
    # The orchestrator service layer replaces this with embedding similarity.
    objective_tokens = set(original_objective.lower().split())

    similarities: list[float] = []
    for output_text in recent_outputs:
        output_tokens = set(output_text.lower().split())
        if not objective_tokens:
            similarities.append(0.0)
            continue

        overlap = len(objective_tokens & output_tokens)
        sim = overlap / max(1, len(objective_tokens))
        similarities.append(round(min(1.0, sim), 4))

    avg_similarity = sum(similarities) / max(1, len(similarities))
    is_drifting = avg_similarity < drift_threshold

    drift_magnitude = max(0.0, 1.0 - avg_similarity)

    return GoalDriftDetection(
        is_drifting=is_drifting,
        similarity_trend=similarities,
        drift_magnitude=round(drift_magnitude, 4),
    )


# ============================================================================
# Step 6: Recommend Action
# ============================================================================


def recommend_action(
    load: CognitiveLoad,
    loops: LoopDetection,
    stall: bool = False,
    oscillation: OscillationDetection | None = None,
    drift: GoalDriftDetection | None = None,
) -> LoadRecommendation:
    """Map current cognitive state to a recommended action.

    Decision logic follows the graduated response ladder:
    - Load < 0.6 AND no anomalies → CONTINUE
    - Load 0.6-0.8 OR minor loop → SIMPLIFY
    - Load > 0.8 OR persistent loop OR goal drift → ESCALATE
    - Load > 0.95 OR unbreakable loop → ABORT
    """
    settings = get_settings().kernel

    # Determine anomaly severity
    has_loop = loops.is_looping
    has_oscillation = oscillation.is_oscillating if oscillation else False
    has_drift = drift.is_drifting if drift else False
    persistent_loop = has_loop and loops.loop_count >= settings.load_loop_repeat_threshold

    # ABORT conditions
    if load.aggregate >= settings.load_threshold_abort or persistent_loop:
        reasoning_parts = []
        if load.aggregate >= settings.load_threshold_abort:
            reasoning_parts.append(f"load critical ({load.aggregate:.2f})")
        if persistent_loop:
            reasoning_parts.append(f"persistent loop ({loops.loop_count}x)")
        return LoadRecommendation(
            action=LoadAction.ABORT,
            reasoning=f"ABORT: {', '.join(reasoning_parts)}",
            load_snapshot=load,
            loop_detected=has_loop,
            stall_detected=stall,
            oscillation_detected=has_oscillation,
            drift_detected=has_drift,
        )

    # ESCALATE conditions
    if (
        load.aggregate >= settings.load_threshold_escalate
        or has_drift
        or (has_loop and loops.loop_count >= 2)
    ):
        reasoning_parts = []
        if load.aggregate >= settings.load_threshold_escalate:
            reasoning_parts.append(f"load high ({load.aggregate:.2f})")
        if has_drift:
            reasoning_parts.append("goal drift detected")
        if has_loop:
            reasoning_parts.append(f"loop detected ({loops.loop_count}x)")
        return LoadRecommendation(
            action=LoadAction.ESCALATE,
            reasoning=f"ESCALATE: {', '.join(reasoning_parts)}",
            load_snapshot=load,
            loop_detected=has_loop,
            stall_detected=stall,
            oscillation_detected=has_oscillation,
            drift_detected=has_drift,
        )

    # SIMPLIFY conditions
    if (
        load.aggregate >= settings.load_threshold_simplify
        or has_loop
        or has_oscillation
        or stall
    ):
        reasoning_parts = []
        if load.aggregate >= settings.load_threshold_simplify:
            reasoning_parts.append(f"load moderate ({load.aggregate:.2f})")
        if has_loop:
            reasoning_parts.append("minor loop")
        if has_oscillation:
            reasoning_parts.append("oscillation")
        if stall:
            reasoning_parts.append("stall detected")
        return LoadRecommendation(
            action=LoadAction.SIMPLIFY,
            reasoning=f"SIMPLIFY: {', '.join(reasoning_parts)}",
            load_snapshot=load,
            loop_detected=has_loop,
            stall_detected=stall,
            oscillation_detected=has_oscillation,
            drift_detected=has_drift,
        )

    # CONTINUE — normal operation
    return LoadRecommendation(
        action=LoadAction.CONTINUE,
        reasoning="Normal operation",
        load_snapshot=load,
    )


# ============================================================================
# Top-Level Orchestrator
# ============================================================================


async def monitor_cognitive_load(
    activation_map: ActivationMap,
    telemetry: CycleTelemetry,
    recent_decisions: list[Decision],
    recent_outputs: list[str] | None = None,
    original_objective: str = "",
    kit: InferenceKit | None = None,
) -> Result:
    """Top-level cognitive load monitor.

    Measures load, runs all detectors, and returns a
    LoadRecommendation via the standard Result protocol.
    """
    ref = _ref("monitor_cognitive_load")
    start = time.perf_counter()

    try:
        # Measure load
        load = measure_load(activation_map, telemetry)

        # Run anomaly detectors
        loops = detect_loop(recent_decisions)
        stall_detected = detect_stall(
            telemetry.cycle_duration_ms,
            telemetry.expected_duration_ms,
        )
        oscillation = detect_oscillation(recent_decisions)

        drift = GoalDriftDetection()
        if recent_outputs and original_objective:
            drift = await detect_goal_drift(recent_outputs, original_objective, kit)

        # Get recommendation
        recommendation = recommend_action(
            load, loops, stall_detected, oscillation, drift,
        )

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)

        signal = create_data_signal(
            data=recommendation.model_dump(),
            schema="LoadRecommendation",
            origin=ref,
            trace_id="",
            tags={
                "action": recommendation.action.value,
                "aggregate_load": f"{load.aggregate:.3f}",
                "loop": str(loops.is_looping),
                "stall": str(stall_detected),
                "oscillation": str(oscillation.is_oscillating),
                "drift": str(drift.is_drifting),
            },
        )

        log.info(
            "Cognitive load monitored",
            action=recommendation.action.value,
            aggregate_load=round(load.aggregate, 3),
            loop=loops.is_looping,
            stall=stall_detected,
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Cognitive load monitoring failed: {exc}",
            source=ref,
            detail={"error_type": type(exc).__name__},
        )
        log.error("Cognitive load monitoring failed", error=str(exc))
        return fail(error=error, metrics=metrics)
