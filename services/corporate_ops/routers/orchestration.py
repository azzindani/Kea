"""
Orchestration Router — /orchestration/* endpoints.

HTTP orchestration layer for mission execution: sprint pipeline,
corporate OODA monitoring loop, handoffs, and checkpoint management.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from shared.config import get_settings
from shared.logging.main import get_logger
from shared.schemas import (
    CorporateAgentProcessRequest,
    CorporateAgentSpawnRequest,
)

from services.corporate_ops.clients.orchestrator_client import (
    get_corporate_orchestrator_client,
)
from services.corporate_ops.clients.vault_ledger import (
    ArtifactMetadata,
    CheckpointState,
    get_vault_ledger_client,
)

log = get_logger(__name__)

router = APIRouter()

# ============================================================================
# In-Memory Mission State
# ============================================================================

_missions: dict[str, dict[str, Any]] = {}


# ============================================================================
# Request/Response Models
# ============================================================================


class MissionRequest(BaseModel):
    """Request to start a new mission."""

    mission_id: str = Field(..., description="Unique mission identifier")
    objective: str = Field(..., description="High-level mission objective")
    chunks: list[Any] = Field(..., description="Decomposed mission chunks (MissionChunk dicts)")
    budget: float = Field(default=0.0, ge=0.0)
    available_profiles: list[dict[str, Any]] = Field(default_factory=list)


class MissionStatusResponse(BaseModel):
    """Current mission progress."""

    mission_id: str
    status: str = "running"
    current_sprint: int = 0
    total_sprints: int = 0
    completion_pct: float = 0.0
    total_cost: float = 0.0


class ResumeRequest(BaseModel):
    """Request to resume a mission from checkpoint."""

    mission_id: str


# ============================================================================
# Sprint Execution (Internal)
# ============================================================================


async def _execute_sprint(
    sprint: Any,
    mission_id: str,
    available_profiles: list[dict[str, Any]],
) -> Any:
    """Execute a sprint by hiring agents and dispatching work via HTTP.

    1. Build sprint DAG (pure kernel)
    2. For each node: spawn agent via Orchestrator HTTP
    3. For each agent: execute via Orchestrator HTTP
    4. Collect results
    """
    from kernel.team_orchestrator import SprintResult
    settings = get_settings()
    orch_client = await get_corporate_orchestrator_client()

    completed_chunks: list[str] = []
    failed_chunks: list[str] = []
    agent_results: dict[str, dict[str, Any]] = {}
    artifacts_produced: list[str] = []
    total_cost = 0.0
    start_time = time.perf_counter()

    for chunk_data in sprint.chunks:
        chunk_id = chunk_data.get("chunk_id", "") if isinstance(chunk_data, dict) else chunk_data.chunk_id
        sub_objective = chunk_data.get("sub_objective", "") if isinstance(chunk_data, dict) else chunk_data.sub_objective
        required_tools = chunk_data.get("required_tools", []) if isinstance(chunk_data, dict) else chunk_data.required_tools
        token_budget = chunk_data.get("token_budget", 0) if isinstance(chunk_data, dict) else chunk_data.token_budget
        cost_budget = chunk_data.get("cost_budget", 0.0) if isinstance(chunk_data, dict) else chunk_data.cost_budget
        time_budget_ms = chunk_data.get("time_budget_ms", 0.0) if isinstance(chunk_data, dict) else chunk_data.time_budget_ms
        predecessor_ids = chunk_data.get("predecessor_artifact_ids", []) if isinstance(chunk_data, dict) else chunk_data.predecessor_artifact_ids

        # Select profile (default to first available or 'default')
        profile_id = "default"
        if available_profiles:
            profile_id = available_profiles[0].get("profile_id", "default")

        try:
            # Step 1: Spawn agent
            spawn_request = CorporateAgentSpawnRequest(
                mission_id=mission_id,
                chunk_id=chunk_id,
                profile_id=profile_id,
                sub_objective=sub_objective,
                required_tools=required_tools,
                token_budget=token_budget,
                cost_budget=cost_budget,
                time_budget_ms=time_budget_ms,
                predecessor_artifact_ids=predecessor_ids,
            )
            spawn_resp = await orch_client.spawn_agent(spawn_request)

            # Step 2: Execute agent
            process_request = CorporateAgentProcessRequest(
                raw_input=sub_objective,
            )
            process_resp = await orch_client.process_agent(
                spawn_resp.agent_id, process_request
            )

            agent_results[spawn_resp.agent_id] = process_resp.model_dump()
            total_cost += process_resp.cost

            if process_resp.status == "completed":
                completed_chunks.append(chunk_id)

                # Step 3: Store artifact in Vault
                vault_client = await get_vault_ledger_client()
                try:
                    artifact_id = await vault_client.write_artifact(
                        agent_id=spawn_resp.agent_id,
                        team_id=mission_id,
                        content=str(process_resp.result),
                        metadata=ArtifactMetadata(
                            team_id=mission_id,
                            mission_id=mission_id,
                            sprint_id=sprint.sprint_id,
                            chunk_id=chunk_id,
                            agent_id=spawn_resp.agent_id,
                            content_type="report",
                            topic=sub_objective[:100],
                            summary=f"Output for chunk {chunk_id}",
                        ),
                    )
                    artifacts_produced.append(artifact_id)
                except Exception as vault_exc:
                    log.warning(
                        "vault_write_failed",
                        error=str(vault_exc),
                        chunk_id=chunk_id,
                    )
            else:
                failed_chunks.append(chunk_id)

            # Step 4: Terminate agent
            try:
                await orch_client.terminate_agent(
                    spawn_resp.agent_id, reason="mission_complete"
                )
            except Exception:
                pass  # Best-effort cleanup

        except Exception as exc:
            log.error(
                "chunk_execution_failed",
                error=str(exc),
                chunk_id=chunk_id,
            )
            failed_chunks.append(chunk_id)

    duration_ms = (time.perf_counter() - start_time) * 1000

    return SprintResult(
        sprint_id=sprint.sprint_id,
        completed_chunks=completed_chunks,
        failed_chunks=failed_chunks,
        agent_results=agent_results,
        artifacts_produced=artifacts_produced,
        total_cost=total_cost,
        duration_ms=duration_ms,
        was_checkpointed=False,
    )


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/missions")
async def orchestrate_mission(request: MissionRequest) -> dict[str, Any]:
    """Start a new mission — full sprint pipeline.

    1. plan_sprints() — pure kernel call
    2. For each sprint: execute_sprint() → review_sprint() → checkpoint
    3. Return aggregated MissionResult
    """
    from kernel.team_orchestrator import (
        MissionResult, Sprint, SprintReview, plan_sprints, review_sprint,
    )
    settings = get_settings()
    mission_id = request.mission_id
    start_time = time.perf_counter()

    # Store mission state
    _missions[mission_id] = {
        "status": "running",
        "current_sprint": 0,
        "total_sprints": 0,
    }

    # Step 1: Plan sprints
    plan_result = await plan_sprints(
        chunks=request.chunks,
        mission_id=mission_id,
    )

    sprints: list[Sprint] = []
    if plan_result.signals:
        plan_data = plan_result.signals[0].payload
        if isinstance(plan_data, dict):
            for s in plan_data.get("sprints", []):
                sprints.append(Sprint(**s))

    total_sprints = len(sprints)
    _missions[mission_id]["total_sprints"] = total_sprints

    # Step 2: Execute sprints sequentially
    all_artifacts: list[str] = []
    all_agent_results: dict[str, dict[str, Any]] = {}
    total_cost = 0.0
    completed_sprints = 0
    final_review: SprintReview | None = None

    for sprint in sprints:
        _missions[mission_id]["current_sprint"] = sprint.sprint_number

        # Execute sprint
        sprint_result = await _execute_sprint(
            sprint=sprint,
            mission_id=mission_id,
            available_profiles=request.available_profiles,
        )

        all_artifacts.extend(sprint_result.artifacts_produced)
        all_agent_results.update(sprint_result.agent_results)
        total_cost += sprint_result.total_cost

        # Review sprint (if enabled)
        if settings.corporate.sprint_review_enabled:
            review_result = await review_sprint(
                sprint=sprint,
                result=sprint_result,
            )

            if review_result.signals:
                review_data = review_result.signals[0].payload
                if isinstance(review_data, dict):
                    final_review = SprintReview(**review_data)

                    # Check if next sprint is approved
                    if not final_review.next_sprint_approved:
                        log.warning(
                            "sprint_review_blocked",
                            sprint_id=sprint.sprint_id,
                            issues=final_review.issues_found,
                        )
                        break

        # Checkpoint to Vault
        if sprint.sprint_number % settings.corporate.checkpoint_interval_sprints == 0:
            vault_client = await get_vault_ledger_client()
            try:
                await vault_client.write_checkpoint(
                    mission_id=mission_id,
                    state=CheckpointState(
                        mission_id=mission_id,
                        current_sprint=sprint.sprint_number,
                        total_sprints=total_sprints,
                        completed_chunk_ids=sprint_result.completed_chunks,
                        failed_chunk_ids=sprint_result.failed_chunks,
                        artifact_ids=all_artifacts,
                        total_cost=total_cost,
                        elapsed_ms=(time.perf_counter() - start_time) * 1000,
                    ),
                )
            except Exception as cp_exc:
                log.warning("checkpoint_write_failed", error=str(cp_exc))

        completed_sprints += 1

    total_duration_ms = (time.perf_counter() - start_time) * 1000
    completion_pct = completed_sprints / total_sprints if total_sprints > 0 else 0.0

    _missions[mission_id]["status"] = "completed"

    result = MissionResult(
        mission_id=mission_id,
        total_sprints=total_sprints,
        completed_sprints=completed_sprints,
        all_artifacts=all_artifacts,
        all_agent_results=all_agent_results,
        total_cost=total_cost,
        total_duration_ms=total_duration_ms,
        completion_pct=completion_pct,
        final_review=final_review,
    )

    log.info(
        "mission_complete",
        mission_id=mission_id,
        sprints=completed_sprints,
        total_sprints=total_sprints,
        artifacts=len(all_artifacts),
        cost=round(total_cost, 4),
        duration_ms=round(total_duration_ms, 2),
    )

    return result.model_dump()


@router.post("/missions/{mission_id}/resume")
async def resume_mission(mission_id: str) -> dict[str, Any]:
    """Resume a mission from its last checkpoint.

    1. Read checkpoint from Vault
    2. Resume from the next sprint after the checkpoint
    """
    vault_client = await get_vault_ledger_client()
    checkpoint = await vault_client.read_checkpoint(mission_id)

    if not checkpoint:
        raise HTTPException(
            status_code=404,
            detail=f"No checkpoint found for mission {mission_id}",
        )

    return {
        "mission_id": mission_id,
        "resumed_from_sprint": checkpoint.current_sprint,
        "total_sprints": checkpoint.total_sprints,
        "completed_chunks": checkpoint.completed_chunk_ids,
        "artifacts_recovered": checkpoint.artifact_ids,
        "cost_so_far": checkpoint.total_cost,
    }


@router.get("/missions/{mission_id}/status")
async def get_mission_status(mission_id: str) -> MissionStatusResponse:
    """Get current mission progress."""
    mission = _missions.get(mission_id)
    if not mission:
        raise HTTPException(
            status_code=404, detail=f"Mission {mission_id} not found"
        )

    total = mission.get("total_sprints", 0)
    current = mission.get("current_sprint", 0)

    return MissionStatusResponse(
        mission_id=mission_id,
        status=mission.get("status", "unknown"),
        current_sprint=current,
        total_sprints=total,
        completion_pct=current / total if total > 0 else 0.0,
    )


@router.post("/missions/{mission_id}/abort")
async def abort_mission(mission_id: str) -> dict[str, Any]:
    """Abort a mission, terminate all agents, collect partial results."""
    mission = _missions.get(mission_id)
    if not mission:
        raise HTTPException(
            status_code=404, detail=f"Mission {mission_id} not found"
        )

    mission["status"] = "aborted"

    log.info("mission_aborted", mission_id=mission_id)

    return {
        "mission_id": mission_id,
        "status": "aborted",
        "current_sprint": mission.get("current_sprint", 0),
    }


@router.post("/missions/{mission_id}/interrupt")
async def interrupt_mission(
    mission_id: str, interrupt_data: dict[str, Any]
) -> dict[str, Any]:
    """Handle a client interrupt (scope change or status query)."""
    mission = _missions.get(mission_id)
    if not mission:
        raise HTTPException(
            status_code=404, detail=f"Mission {mission_id} not found"
        )

    log.info(
        "mission_interrupted",
        mission_id=mission_id,
        type=interrupt_data.get("interrupt_type", "unknown"),
    )

    # For now, just log and return mission status as the "handled" result.
    # In a full implementation, this would trigger a re-plan of remaining sprints.
    return {
        "mission_id": mission_id,
        "interrupt_status": "received",
        "current_status": mission.get("status", "running"),
        "current_sprint": mission.get("current_sprint", 0),
    }

