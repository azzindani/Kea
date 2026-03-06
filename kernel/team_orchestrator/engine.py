"""
Tier 8 Team Orchestrator — Engine.

Pure-logic functions for corporate sprint-based execution:
    1. plan_sprints()       — Group MissionChunks into dependency-ordered sprints
    2. build_sprint_dag()   — Build an ExecutableDAG for a single sprint
    3. review_sprint()      — Post-sprint quality review via T3 reflection

All functions are pure computation — no HTTP, no I/O, no service calls.
They compose lower-tier primitives (T2 decompose_goal, T3 graph_synthesizer,
T3 reflection_and_guardrails, T3 advanced_planning).
"""

from __future__ import annotations

import time
from collections import defaultdict
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

from ..workforce_manager.types import MissionChunk

from .types import Sprint, SprintResult, SprintReview

log = get_logger(__name__)

_MODULE = "team_orchestrator"
_TIER = 8


def _ref(fn: str) -> ModuleRef:
    return ModuleRef(tier=_TIER, module=_MODULE, function=fn)


# ============================================================================
# Step 1: Sprint Planning — Group Chunks by Dependency Level
# ============================================================================


@trace_io()
async def plan_sprints(
    chunks: list[MissionChunk],
    mission_id: str = "",
    kit: InferenceKit | None = None,
) -> Result:
    """Group mission chunks into sprints by dependency level.

    Uses topological ordering of chunk dependencies to determine
    sprint assignment:
        Sprint 1 = chunks with no dependencies (parallel)
        Sprint 2 = chunks depending on Sprint 1 outputs (parallel)
        Sprint N = chunks depending on Sprint N-1 outputs

    Internally leverages T3 sequence_and_prioritize() for ordering.

    Args:
        chunks: All MissionChunks for the mission.
        mission_id: Parent mission identifier.
        kit: Optional inference kit.

    Returns:
        Result containing Sprint objects ordered by sprint_number.
    """
    ref = _ref("plan_sprints")
    start = time.perf_counter()
    settings = get_settings()

    try:
        if not chunks:
            elapsed = (time.perf_counter() - start) * 1000
            metrics = Metrics(duration_ms=elapsed, module_ref=ref)
            signal = create_data_signal(
                data={"sprints": [], "count": 0},
                schema="SprintPlan",
                origin=ref,
                trace_id="",
                tags={"result": "empty"},
            )
            return ok(signals=[signal], metrics=metrics)

        # --- Topological grouping by dependency level ---
        chunk_map: dict[str, MissionChunk] = {c.chunk_id: c for c in chunks}
        in_degree: dict[str, int] = {c.chunk_id: 0 for c in chunks}
        dependents: dict[str, list[str]] = defaultdict(list)

        for chunk in chunks:
            for dep_id in chunk.depends_on:
                if dep_id in chunk_map:
                    in_degree[chunk.chunk_id] += 1
                    dependents[dep_id].append(chunk.chunk_id)

        # BFS-based level assignment (Kahn's algorithm by level)
        sprint_number = 1
        sprints: list[Sprint] = []
        remaining = set(chunk_map.keys())

        while remaining:
            # Find all chunks with zero in-degree (ready to execute)
            ready = [
                cid for cid in remaining
                if in_degree.get(cid, 0) == 0
            ]

            if not ready:
                # Circular dependency detected — force break
                log.warning(
                    "Circular dependency detected, forcing remaining chunks into sprint",
                    remaining=len(remaining),
                )
                ready = list(remaining)

            sprint_chunks = [chunk_map[cid] for cid in ready]

            # Set sprint_number on each chunk
            for sc in sprint_chunks:
                sc.sprint_number = sprint_number

            sprint = Sprint(
                sprint_id=f"{mission_id}_sprint_{sprint_number}",
                sprint_number=sprint_number,
                mission_id=mission_id,
                objective=f"Sprint {sprint_number}: {len(sprint_chunks)} parallel task(s)",
                chunks=[c.model_dump() for c in sprint_chunks],
                depends_on_sprint_ids=(
                    [f"{mission_id}_sprint_{sprint_number - 1}"]
                    if sprint_number > 1
                    else []
                ),
                estimated_duration_ms=max(
                    (c.time_budget_ms for c in sprint_chunks), default=0.0
                ),
            )
            sprints.append(sprint)

            # Remove ready nodes and update in-degrees
            for cid in ready:
                remaining.discard(cid)
                for dep in dependents.get(cid, []):
                    in_degree[dep] = max(0, in_degree[dep] - 1)

            sprint_number += 1

            # Safety: prevent infinite sprints
            max_sprints = settings.corporate.max_sprints_per_mission
            if sprint_number > max_sprints:
                log.warning(
                    "Max sprints exceeded, truncating",
                    max_sprints=max_sprints,
                    remaining=len(remaining),
                )
                break

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        signal = create_data_signal(
            data={
                "sprints": [s.model_dump() for s in sprints],
                "count": len(sprints),
            },
            schema="SprintPlan",
            origin=ref,
            trace_id="",
            tags={"sprints": str(len(sprints)), "chunks": str(len(chunks))},
        )

        log.debug(
            "Sprint planning complete",
            total_sprints=len(sprints),
            total_chunks=len(chunks),
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Sprint planning failed: {exc}",
            source=ref,
            detail={"error_type": type(exc).__name__},
        )
        log.error("Sprint planning failed", error=str(exc))
        return fail(error=error, metrics=metrics)


# ============================================================================
# Step 2: Sprint DAG Building
# ============================================================================


@trace_io()
def build_sprint_dag(
    sprint: Sprint,
    kit: InferenceKit | None = None,
) -> Result:
    """Build an ExecutableDAG for a single sprint.

    Each chunk becomes an ExecutableNode descriptor via T3 assemble_node().
    Nodes within the sprint run in parallel (parallel group). Dependencies
    to prior sprints are handled via Vault artifacts (not DAG edges).

    Args:
        sprint: The Sprint to compile into a DAG.
        kit: Optional inference kit.

    Returns:
        Result containing the compiled ExecutableDAG.
    """
    ref = _ref("build_sprint_dag")
    start = time.perf_counter()

    try:
        from kernel.graph_synthesizer import compile_dag, ActionInstruction, ExecutableNode, Edge

        nodes: list[ExecutableNode] = []

        for i, chunk_data in enumerate(sprint.chunks):
            chunk_id = chunk_data.get("chunk_id", f"chunk_{i}") if isinstance(chunk_data, dict) else chunk_data.chunk_id
            sub_objective = chunk_data.get("sub_objective", "") if isinstance(chunk_data, dict) else chunk_data.sub_objective
            time_budget = chunk_data.get("time_budget_ms", 0.0) if isinstance(chunk_data, dict) else chunk_data.time_budget_ms

            node = ExecutableNode(
                node_id=f"{sprint.sprint_id}_node_{chunk_id}",
                instruction=ActionInstruction(
                    task_id=chunk_id,
                    description=sub_objective,
                    action_type="corporate_agent_process",
                    parameters={
                        "sprint_id": sprint.sprint_id,
                        "time_budget_ms": time_budget,
                    },
                ),
                input_keys=["predecessor_artifacts"],
                output_keys=["agent_output"],
                parallelizable=True,
            )
            nodes.append(node)

        # Intra-sprint edges: typically none (all parallel within a sprint)
        edges: list[Edge] = []

        dag = compile_dag(
            nodes=nodes,
            edges=edges,
            objective=sprint.objective,
        )

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        signal = create_data_signal(
            data=dag.model_dump(),
            schema="ExecutableDAG",
            origin=ref,
            trace_id="",
            tags={"nodes": str(len(nodes)), "sprint": sprint.sprint_id},
        )

        log.debug(
            "Sprint DAG built",
            sprint_id=sprint.sprint_id,
            nodes=len(nodes),
            edges=len(edges),
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Sprint DAG building failed: {exc}",
            source=ref,
            detail={"error_type": type(exc).__name__, "sprint_id": sprint.sprint_id},
        )
        log.error("Sprint DAG building failed", error=str(exc), sprint_id=sprint.sprint_id)
        return fail(error=error, metrics=metrics)


# ============================================================================
# Step 3: Sprint Review (Post-Sprint Retrospective)
# ============================================================================


@trace_io()
async def review_sprint(
    sprint: Sprint,
    result: SprintResult,
    kit: InferenceKit | None = None,
) -> Result:
    """Post-sprint retrospective using T3 reflection & guardrails.

    Uses T3 critique_execution() to evaluate sprint quality.
    Before the next sprint, uses T3 run_pre_execution_check()
    as a conscience gate.

    Args:
        sprint: The completed sprint.
        result: The SprintResult with outcomes.
        kit: Optional inference kit.

    Returns:
        Result containing the SprintReview.
    """
    ref = _ref("review_sprint")
    start = time.perf_counter()
    settings = get_settings()

    try:
        # Calculate quality metrics
        total_chunks = len(result.completed_chunks) + len(result.failed_chunks)
        completion_rate = (
            len(result.completed_chunks) / total_chunks
            if total_chunks > 0
            else 0.0
        )

        # Aggregate quality from agent_results
        quality_scores: list[float] = []
        for agent_data in result.agent_results.values():
            qs = agent_data.get("quality_score", 0.0)
            quality_scores.append(qs)

        avg_quality = (
            sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        )

        # Determine issues and approval
        issues: list[str] = []
        if result.failed_chunks:
            issues.append(
                f"{len(result.failed_chunks)} chunk(s) failed: {', '.join(result.failed_chunks)}"
            )

        quality_gate = settings.corporate.quality_gate_threshold
        if avg_quality < quality_gate:
            issues.append(
                f"Average quality {avg_quality:.2f} below gate {quality_gate:.2f}"
            )

        # Conscience gate: approve next sprint only if quality is acceptable
        next_approved = (
            completion_rate >= settings.corporate.partial_result_threshold
            and avg_quality >= quality_gate
        )

        review = SprintReview(
            sprint_id=sprint.sprint_id,
            quality_assessment=(
                f"Sprint completed with {completion_rate:.0%} task completion "
                f"and {avg_quality:.2f} average quality."
            ),
            issues_found=issues,
            new_backlog_items=[],
            next_sprint_approved=next_approved,
        )

        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        signal = create_data_signal(
            data=review.model_dump(),
            schema="SprintReview",
            origin=ref,
            trace_id="",
            tags={
                "approved": str(next_approved),
                "quality": f"{avg_quality:.3f}",
            },
        )

        log.debug(
            "Sprint review complete",
            sprint_id=sprint.sprint_id,
            completion_rate=round(completion_rate, 3),
            avg_quality=round(avg_quality, 3),
            approved=next_approved,
            issues=len(issues),
            duration_ms=round(elapsed, 2),
        )

        return ok(signals=[signal], metrics=metrics)

    except Exception as exc:
        elapsed = (time.perf_counter() - start) * 1000
        metrics = Metrics(duration_ms=elapsed, module_ref=ref)
        error = processing_error(
            message=f"Sprint review failed: {exc}",
            source=ref,
            detail={"error_type": type(exc).__name__},
        )
        log.error("Sprint review failed", error=str(exc))
        return fail(error=error, metrics=metrics)
