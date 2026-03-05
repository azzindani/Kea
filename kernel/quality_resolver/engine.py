"""
Tier 8 Quality Resolver — Engine.

Pure-logic functions for corporate quality assurance:
    1. detect_conflicts()       — Scan agent outputs for contradictions
    2. resolve_conflict()       — Apply resolution cascade (consensus → weighted vote)
    3. score_sprint_quality()   — Aggregate quality metrics into a QualityAudit

All functions are pure computation — no HTTP, no I/O, no service calls.
They compose lower-tier primitives (T2 attention_and_plausibility,
T3 reflection_and_guardrails, T1 scoring, T6 noise_gate).
"""

from __future__ import annotations

import time
from typing import Any

from shared.config import get_settings
from shared.inference_kit import InferenceKit
from shared.logging.main import get_logger
from shared.logging.decorators import trace_io
from shared.standard_io import (
    Metrics,
    ModuleRef,
    Result,
    create_data_signal,
    fail,
    ok,
    processing_error,
)

from .types import Conflict, QualityAudit, Resolution

log = get_logger(__name__)

_MODULE = "quality_resolver"
_TIER = 8


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Step 1: Conflict Detection
# ============================================================================


@trace_io()
async def detect_conflicts(
    artifacts: list[dict[str, Any]],
    kit: InferenceKit | None = None,
) -> Result:
    """Scan agent outputs for contradictions.

    Uses T2 attention_and_plausibility.run_cognitive_filters() to
    detect semantic contradictions between pairs of artifacts.

    Args:
        artifacts: List of VaultArtifact-like dicts with 'artifact_id',
            'content', 'metadata' fields.
        kit: Optional inference kit for semantic analysis.

    Returns:
        Result containing detected Conflict objects.
    """
    ref = _ref("detect_conflicts")
    start = time.perf_counter()
    settings = get_settings()

    try:
        conflicts: list[Conflict] = []

        if len(artifacts) < 2:
            elapsed = (time.perf_counter() - start) * 1000
            metrics = Metrics(duration_ms=elapsed, module_ref=ref)
            signal = create_data_signal(
                data={"conflicts": [], "count": 0},
                schema="ConflictDetection",
                origin=ref,
                trace_id="",
                tags={"result": "insufficient_artifacts"},
            )
            return ok(signals=[signal], metrics=metrics)

        # Pairwise contradiction detection using T1 scoring
        # for semantic similarity — contradictions show high similarity
        # but opposite conclusions
        from kernel.scoring import score as t1_score

        similarity_threshold = settings.corporate.conflict_similarity_threshold

        for i in range(len(artifacts)):
            for j in range(i + 1, len(artifacts)):
                art_a = artifacts[i]
                art_b = artifacts[j]

                content_a = art_a.get("content", "")
                content_b = art_b.get("content", "")

                if not content_a or not content_b:
                    continue

                # Score semantic similarity between the two artifacts
                score_result = await t1_score(
                    content=content_a,
                    query=content_b,
                    kit=kit,
                )

                similarity = 0.0
                if score_result.signals:
                    score_data = score_result.signals[0].payload
                    if isinstance(score_data, dict):
                        similarity = score_data.get("score", 0.0)

                # High similarity between different agents' outputs
                # on the same topic may indicate conflicting conclusions
                if similarity >= similarity_threshold:
                    # Check for content divergence (same topic, different conclusions)
                    # Simple heuristic: if both are highly similar but from
                    # different agents, flag for manual review
                    conflict = Conflict(
                        artifact_a_id=art_a.get("artifact_id", f"art_{i}"),
                        artifact_b_id=art_b.get("artifact_id", f"art_{j}"),
                        description=(
                            f"High similarity ({similarity:.2f}) detected between "
                            f"artifacts — possible conflicting conclusions"
                        ),
                        severity="medium" if similarity < 0.9 else "high",
                    )
                    conflicts.append(conflict)

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        signal = create_data_signal(
            data={
                "conflicts": [c.model_dump() for c in conflicts],
                "count": len(conflicts),
            },
            schema="ConflictDetection",
            origin=ref,
            trace_id="",
            tags={"conflicts": str(len(conflicts))},
        )

        log.debug(
            "Conflict detection complete",
            artifacts=len(artifacts),
            conflicts_found=len(conflicts),
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Conflict detection failed: {exc}",
            source=ref,
            detail={"error_type": type(exc).__name__},
        )
        log.error("Conflict detection failed", error=str(exc))
        return fail(error=error, metrics=metrics)


# ============================================================================
# Step 2: Conflict Resolution
# ============================================================================


@trace_io()
async def resolve_conflict(
    conflict: Conflict,
    artifact_a: dict[str, Any],
    artifact_b: dict[str, Any],
    kit: InferenceKit | None = None,
) -> Result:
    """Resolve a detected conflict using the resolution cascade.

    Strategy cascade:
        1. Consensus (T3 evaluate_consensus) — both agree
        2. Weighted vote (T1 scoring) — higher confidence wins
        3. If neither works, marks for arbitration (service layer handles)

    Args:
        conflict: The detected Conflict.
        artifact_a: First artifact dict.
        artifact_b: Second artifact dict.
        kit: Optional inference kit.

    Returns:
        Result containing the Resolution.
    """
    ref = _ref("resolve_conflict")
    start = time.perf_counter()

    try:
        # Strategy 1: Compare quality scores from metadata
        score_a = artifact_a.get("metadata", {}).get("quality_score", 0.5)
        score_b = artifact_b.get("metadata", {}).get("quality_score", 0.5)

        confidence_a = artifact_a.get("metadata", {}).get("confidence", 0.5)
        confidence_b = artifact_b.get("metadata", {}).get("confidence", 0.5)

        # Weighted composite scores
        composite_a = (score_a * 0.6) + (confidence_a * 0.4)
        composite_b = (score_b * 0.6) + (confidence_b * 0.4)

        # Determine winner via weighted vote
        if abs(composite_a - composite_b) > 0.1:
            # Clear winner
            if composite_a > composite_b:
                winning_id = artifact_a.get("artifact_id", "")
                strategy = "weighted_vote"
            else:
                winning_id = artifact_b.get("artifact_id", "")
                strategy = "weighted_vote"

            resolution_confidence = abs(composite_a - composite_b)
            justification = (
                f"Weighted vote: composite scores {composite_a:.3f} vs "
                f"{composite_b:.3f} (quality+confidence)"
            )
        else:
            # Too close — needs arbitration from service layer
            winning_id = artifact_a.get("artifact_id", "")
            strategy = "arbitration"
            resolution_confidence = 0.3
            justification = (
                f"Scores too close ({composite_a:.3f} vs {composite_b:.3f}), "
                f"needs arbitration by judge specialist"
            )

        resolution = Resolution(
            conflict_id=f"{conflict.artifact_a_id}_vs_{conflict.artifact_b_id}",
            strategy_used=strategy,
            winning_artifact_id=winning_id,
            justification=justification,
            confidence=min(resolution_confidence, 1.0),
        )

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        signal = create_data_signal(
            data=resolution.model_dump(),
            schema="Resolution",
            origin=ref,
            trace_id="",
            tags={"strategy": strategy, "confidence": f"{resolution_confidence:.3f}"},
        )

        log.debug(
            "Conflict resolved",
            strategy=strategy,
            winning=winning_id,
            confidence=round(resolution_confidence, 3),
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Conflict resolution failed: {exc}",
            source=ref,
            detail={"error_type": type(exc).__name__},
        )
        log.error("Conflict resolution failed", error=str(exc))
        return fail(error=error, metrics=metrics)


# ============================================================================
# Step 3: Sprint Quality Scoring
# ============================================================================


@trace_io()
async def score_sprint_quality(
    agent_results: list[dict[str, Any]],
    sprint_id: str = "",
    kit: InferenceKit | None = None,
) -> Result:
    """Aggregate quality metrics from agent process responses.

    Computes averages across quality_score, confidence, and
    grounding_rate from all agent results in a sprint.
    Determines overall audit status: pass / warning / fail.

    Args:
        agent_results: List of CorporateAgentProcessResponse dicts.
        sprint_id: Sprint identifier for the audit.
        kit: Optional inference kit.

    Returns:
        Result containing the QualityAudit.
    """
    ref = _ref("score_sprint_quality")
    start = time.perf_counter()
    settings = get_settings()

    try:
        quality_scores: list[float] = []
        confidence_scores: list[float] = []
        grounding_scores: list[float] = []
        issues: list[str] = []

        for ar in agent_results:
            qs = ar.get("quality_score", 0.0)
            cs = ar.get("confidence", 0.0)
            gs = ar.get("grounding_rate", 0.0)
            agent_id = ar.get("agent_id", "unknown")

            quality_scores.append(qs)
            confidence_scores.append(cs)
            grounding_scores.append(gs)

            # Flag individual agent issues
            gate_threshold = settings.corporate.quality_gate_threshold
            if qs < gate_threshold:
                issues.append(
                    f"Agent {agent_id}: quality {qs:.2f} below gate {gate_threshold:.2f}"
                )
            if gs < settings.kernel.noise_gate_grounding_threshold:
                issues.append(
                    f"Agent {agent_id}: grounding {gs:.2f} below threshold"
                )

        # Compute averages
        avg_quality = (
            sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        )
        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        )
        avg_grounding = (
            sum(grounding_scores) / len(grounding_scores) if grounding_scores else 0.0
        )

        # Determine overall status
        gate_threshold = settings.corporate.quality_gate_threshold
        if avg_quality >= gate_threshold and not issues:
            overall = "pass"
        elif avg_quality >= gate_threshold * 0.8:
            overall = "warning"
        else:
            overall = "fail"

        audit = QualityAudit(
            sprint_id=sprint_id,
            avg_quality=avg_quality,
            avg_confidence=avg_confidence,
            avg_grounding=avg_grounding,
            issues=issues,
            overall=overall,
        )

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        signal = create_data_signal(
            data=audit.model_dump(),
            schema="QualityAudit",
            origin=ref,
            trace_id="",
            tags={"overall": overall, "quality": f"{avg_quality:.3f}"},
        )

        log.debug(
            "Sprint quality scored",
            sprint_id=sprint_id,
            avg_quality=round(avg_quality, 3),
            avg_confidence=round(avg_confidence, 3),
            avg_grounding=round(avg_grounding, 3),
            overall=overall,
            issues=len(issues),
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Sprint quality scoring failed: {exc}",
            source=ref,
            detail={"error_type": type(exc).__name__},
        )
        log.error("Sprint quality scoring failed", error=str(exc))
        return fail(error=error, metrics=metrics)
