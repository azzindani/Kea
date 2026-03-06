"""
Tier 8 Workforce Manager — Engine.

Pure-logic functions for corporate workforce management:
    1. match_specialist()         — Find best CognitiveProfile for a MissionChunk
    2. evaluate_performance()     — Extract metrics from agent process response
    3. compute_scale_decisions()  — Decide HIRE/FIRE/REASSIGN/HOLD based on state

All functions are pure computation — no HTTP, no I/O, no service calls.
They compose lower-tier primitives (T1 scoring, T6 self_model).
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

from .types import (
    AgentHandle,
    AgentStatus,
    MissionChunk,
    PerformanceSnapshot,
    ProfileMatch,
    ScaleAction,
    ScaleDecision,
    WorkforcePool,
)

log = get_logger(__name__)

_MODULE = "workforce_manager"
_TIER = 8


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Step 1: Specialist Profile Matching
# ============================================================================


@trace_io()
async def match_specialist(
    chunk: MissionChunk,
    available_profiles: list[dict[str, Any]],
    kit: InferenceKit | None = None,
) -> Result:
    """Find the best specialist profile for a mission chunk.

    Uses T1 scoring.score() to evaluate skill overlap between chunk
    requirements and profile capabilities. Returns the highest-scoring
    match. If no match exceeds threshold, returns requires_new_profile=True.

    Args:
        chunk: The mission chunk needing a specialist.
        available_profiles: List of profile dicts with 'profile_id',
            'skills', 'role_name' fields.
        kit: Optional inference kit for embedding-based scoring.

    Returns:
        Result containing the ProfileMatch signal.
    """
    ref = _ref("match_specialist")
    start = time.perf_counter()
    settings = get_settings()

    try:
        from kernel.scoring import score as t1_score, Constraint

        if not available_profiles:
            match = ProfileMatch(
                agent_profile_id="none",
                chunk_id=chunk.chunk_id,
                skill_score=0.0,
                composite_score=0.0,
                requires_new_profile=True,
            )
            elapsed = (time.perf_counter() - start) * 1000
            metrics = Metrics(duration_ms=elapsed, module_ref=ref)
            signal = create_data_signal(
                data=match.model_dump(),
                schema="ProfileMatch",
                origin=ref,
                trace_id="",
                tags={"match": "no_profiles"},
            )
            return ok(signals=[signal], metrics=metrics)

        # Build the query from chunk requirements
        query = f"{chunk.domain} {chunk.sub_objective} {' '.join(chunk.required_skills)}"

        best_score = 0.0
        best_profile_id = ""

        for profile in available_profiles:
            profile_id = profile.get("profile_id", "")
            skills = profile.get("skills", [])
            role_name = profile.get("role_name", "")

            # Build content from profile capabilities
            content = f"{role_name} {' '.join(skills)}"

            # Use T1 scoring for hybrid evaluation
            score_result = await t1_score(
                content=content,
                query=query,
                kit=kit,
            )

            # Extract score from result signals
            score_value = 0.0
            if score_result.signals:
                score_data = score_result.signals[0].body.get("data", {})
                if isinstance(score_data, dict):
                    score_value = score_data.get("score", 0.0)

            if score_value > best_score:
                best_score = score_value
                best_profile_id = profile_id

        # Determine threshold from config
        fire_threshold = settings.corporate.agent_fire_quality_threshold
        requires_new = best_score < fire_threshold

        match = ProfileMatch(
            agent_profile_id=best_profile_id or "none",
            chunk_id=chunk.chunk_id,
            skill_score=best_score,
            composite_score=best_score,
            requires_new_profile=requires_new,
        )

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        signal = create_data_signal(
            data=match.model_dump(),
            schema="ProfileMatch",
            origin=ref,
            trace_id="",
            tags={"score": f"{best_score:.3f}", "new_profile": str(requires_new)},
        )

        log.debug(
            "Profile matching complete",
            chunk_id=chunk.chunk_id,
            best_profile=best_profile_id,
            score=round(best_score, 3),
            requires_new=requires_new,
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Profile matching failed: {exc}",
            source=ref,
            detail={"error_type": type(exc).__name__},
        )
        log.error("Profile matching failed", error=str(exc))
        return fail(error=error, metrics=metrics)


# ============================================================================
# Step 2: Performance Evaluation
# ============================================================================


@trace_io()
def evaluate_performance(
    handle: AgentHandle,
    result: dict[str, Any],
) -> PerformanceSnapshot:
    """Extract performance metrics from an Orchestrator agent process response.

    Pure extraction — no new computation logic. Maps the HTTP response
    fields from CorporateAgentProcessResponse into a PerformanceSnapshot.

    Args:
        handle: The AgentHandle of the specialist.
        result: The CorporateAgentProcessResponse as a dict.

    Returns:
        PerformanceSnapshot with extracted metrics.
    """
    return PerformanceSnapshot(
        agent_id=handle.agent_id,
        quality_score=result.get("quality_score", 0.0),
        confidence=result.get("confidence", 0.0),
        grounding_rate=result.get("grounding_rate", 0.0),
        latency_ms=result.get("duration_ms", 0.0),
        cost=result.get("cost", 0.0),
    )


# ============================================================================
# Step 3: Scaling Decision Computation
# ============================================================================


@trace_io()
def compute_scale_decisions(
    pool: WorkforcePool,
    pending_chunks: list[MissionChunk],
    performance: list[PerformanceSnapshot],
    hardware_profile: dict[str, Any],
) -> list[ScaleDecision]:
    """Pure computation of scaling decisions.

    Checks: pending work queue, agent utilization, hardware resources,
    budget remaining. Returns decisions: HIRE_MORE, FIRE_IDLE,
    REASSIGN, HOLD. Does NOT execute the decisions — the service
    layer does.

    Args:
        pool: Current workforce pool state.
        pending_chunks: Chunks not yet assigned to agents.
        performance: Recent performance snapshots for active agents.
        hardware_profile: Hardware resource info (safe_parallel_limit, etc.).

    Returns:
        List of ScaleDecision objects for the service layer to execute.
    """
    settings = get_settings()
    decisions: list[ScaleDecision] = []

    safe_parallel_limit = hardware_profile.get("safe_parallel_limit", 1)
    max_concurrent = settings.corporate.max_concurrent_agents

    # Build a performance lookup
    perf_by_agent: dict[str, PerformanceSnapshot] = {
        p.agent_id: p for p in performance
    }

    # Count active agents
    active_agents = [
        h for h in pool.agents.values() if h.status == AgentStatus.ACTIVE
    ]

    # --- Decision 1: Fire underperforming agents ---
    fire_threshold = settings.corporate.agent_fire_quality_threshold
    for agent in active_agents:
        perf = perf_by_agent.get(agent.agent_id)
        if perf and perf.quality_score < fire_threshold:
            decisions.append(
                ScaleDecision(
                    action=ScaleAction.FIRE_IDLE,
                    target_agent_id=agent.agent_id,
                    target_chunk_id=agent.chunk_id,
                    reason=f"Quality score {perf.quality_score:.2f} below threshold {fire_threshold:.2f}",
                )
            )

    # --- Decision 2: Hire more for pending chunks ---
    headroom = min(safe_parallel_limit, max_concurrent) - len(active_agents)
    if headroom > 0 and pending_chunks and pool.budget_remaining > 0:
        hirable = min(headroom, len(pending_chunks))
        for chunk in pending_chunks[:hirable]:
            decisions.append(
                ScaleDecision(
                    action=ScaleAction.HIRE_MORE,
                    target_agent_id=None,
                    target_chunk_id=chunk.chunk_id,
                    reason=f"Pending chunk '{chunk.chunk_id}' needs a specialist",
                )
            )

    # --- Decision 3: Hold if no pending work and agents are performing well ---
    if not pending_chunks and not decisions:
        decisions.append(
            ScaleDecision(
                action=ScaleAction.HOLD,
                target_agent_id=None,
                target_chunk_id=None,
                reason="No pending work and all agents performing within thresholds",
            )
        )

    log.debug(
        "Scale decisions computed",
        active_agents=len(active_agents),
        pending_chunks=len(pending_chunks),
        decisions=len(decisions),
        headroom=headroom if pending_chunks else 0,
    )

    return decisions
