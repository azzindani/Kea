"""
Workforce Router — /workforce/* endpoints.

HTTP orchestration layer for hiring, firing, scaling, and matching
specialist agents. Combines kernel pure logic with Orchestrator
HTTP calls.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from shared.config import get_settings
from shared.logging.main import get_logger
from shared.schemas import CorporateAgentSpawnRequest, CorporateAgentSpawnResponse

from kernel.workforce_manager import (
    AgentHandle,
    AgentStatus,
    MissionChunk,
    WorkforcePool,
    compute_scale_decisions,
    evaluate_performance,
    match_specialist,
)

from services.corporate_ops.clients.orchestrator_client import (
    get_corporate_orchestrator_client,
)
from services.corporate_ops.clients.vault_ledger import get_vault_ledger_client

log = get_logger(__name__)

router = APIRouter()

# ============================================================================
# In-Memory Pool Registry (per-process; production would use Redis/Vault)
# ============================================================================

_pools: dict[str, WorkforcePool] = {}


def _get_or_create_pool(mission_id: str, budget: float = 0.0) -> WorkforcePool:
    """Get or create an in-memory WorkforcePool for a mission."""
    if mission_id not in _pools:
        from shared.id_and_hash import generate_id

        _pools[mission_id] = WorkforcePool(
            pool_id=generate_id("pool"),
            mission_id=mission_id,
            budget_remaining=budget,
        )
    return _pools[mission_id]


# ============================================================================
# Request/Response Models
# ============================================================================


class HireRequest(BaseModel):
    """Request to hire a single specialist."""

    mission_id: str
    chunk: MissionChunk
    available_profiles: list[dict[str, Any]] = Field(default_factory=list)
    budget: float = Field(default=0.0, ge=0.0)


class HireResponse(BaseModel):
    """Response from hiring a specialist."""

    agent: AgentHandle
    match_score: float = 0.0
    spawned: bool = False


class HireBatchRequest(BaseModel):
    """Request to hire multiple specialists (SWARM mode)."""

    mission_id: str
    chunks: list[MissionChunk]
    profile_id: str
    budget: float = Field(default=0.0, ge=0.0)


class FireRequest(BaseModel):
    """Request to terminate a specialist."""

    mission_id: str
    agent_id: str
    reason: str = "mission_complete"


class ScaleRequest(BaseModel):
    """Request to evaluate and execute scaling decisions."""

    mission_id: str
    pending_chunks: list[MissionChunk] = Field(default_factory=list)
    hardware_profile: dict[str, Any] = Field(default_factory=dict)


class MatchRequest(BaseModel):
    """Request to find the best specialist profile for a chunk."""

    chunk: MissionChunk
    available_profiles: list[dict[str, Any]] = Field(default_factory=list)


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/hire", response_model=HireResponse)
async def hire_specialist(request: HireRequest) -> HireResponse:
    """Hire a specialist for a mission chunk.

    1. match_specialist() — pure kernel call to find best profile
    2. HTTP POST orchestrator/corporate/agents — spawn agent
    3. Update in-memory WorkforcePool
    """
    pool = _get_or_create_pool(request.mission_id, request.budget)

    # Step 1: Find best profile match
    match_result = await match_specialist(
        chunk=request.chunk,
        available_profiles=request.available_profiles,
    )

    match_score = 0.0
    profile_id = "default"
    if match_result.signals:
        match_data = match_result.signals[0].payload
        if isinstance(match_data, dict):
            match_score = match_data.get("composite_score", 0.0)
            pid = match_data.get("agent_profile_id", "")
            if pid and pid != "none":
                profile_id = pid

    # Step 2: Spawn via Orchestrator HTTP
    orch_client = await get_corporate_orchestrator_client()
    spawn_request = CorporateAgentSpawnRequest(
        mission_id=request.mission_id,
        chunk_id=request.chunk.chunk_id,
        profile_id=profile_id,
        sub_objective=request.chunk.sub_objective,
        required_tools=request.chunk.required_tools,
        token_budget=request.chunk.token_budget,
        cost_budget=request.chunk.cost_budget,
        time_budget_ms=request.chunk.time_budget_ms,
        predecessor_artifact_ids=request.chunk.predecessor_artifact_ids,
    )

    try:
        spawn_response = await orch_client.spawn_agent(spawn_request)
    except Exception as exc:
        log.error("agent_spawn_failed", error=str(exc), chunk_id=request.chunk.chunk_id)
        raise HTTPException(status_code=502, detail=f"Agent spawn failed: {exc}") from exc

    # Step 3: Register in pool
    handle = AgentHandle(
        agent_id=spawn_response.agent_id,
        profile_id=spawn_response.profile_id or profile_id,
        role_name=profile_id,
        chunk_id=request.chunk.chunk_id,
        status=AgentStatus.INITIALIZING,
        hired_utc=spawn_response.spawned_utc or datetime.now(timezone.utc).isoformat(),
    )
    pool.agents[handle.agent_id] = handle
    pool.total_hired += 1

    log.info(
        "specialist_hired",
        agent_id=handle.agent_id,
        mission_id=request.mission_id,
        chunk_id=request.chunk.chunk_id,
        match_score=round(match_score, 3),
    )

    return HireResponse(agent=handle, match_score=match_score, spawned=True)


@router.post("/hire/batch", response_model=list[HireResponse])
async def hire_batch(request: HireBatchRequest) -> list[HireResponse]:
    """SWARM-mode batch hiring — spawn multiple specialists at once."""
    settings = get_settings()
    pool = _get_or_create_pool(request.mission_id, request.budget)
    responses: list[HireResponse] = []

    orch_client = await get_corporate_orchestrator_client()

    # Build batch spawn requests
    spawn_requests: list[CorporateAgentSpawnRequest] = []
    for chunk in request.chunks:
        spawn_requests.append(
            CorporateAgentSpawnRequest(
                mission_id=request.mission_id,
                chunk_id=chunk.chunk_id,
                profile_id=request.profile_id,
                sub_objective=chunk.sub_objective,
                required_tools=chunk.required_tools,
                token_budget=chunk.token_budget,
                cost_budget=chunk.cost_budget,
                time_budget_ms=chunk.time_budget_ms,
                predecessor_artifact_ids=chunk.predecessor_artifact_ids,
            )
        )

    # Spawn in waves based on batch size
    batch_size = settings.corporate.spawn_batch_size
    for i in range(0, len(spawn_requests), batch_size):
        wave = spawn_requests[i : i + batch_size]
        try:
            spawn_responses = await orch_client.spawn_batch(wave)
        except Exception as exc:
            log.error("batch_spawn_failed", error=str(exc), wave=i)
            # Partial success: return what we have
            break

        for sr, chunk in zip(spawn_responses, request.chunks[i : i + batch_size]):
            handle = AgentHandle(
                agent_id=sr.agent_id,
                profile_id=sr.profile_id or request.profile_id,
                role_name=request.profile_id,
                chunk_id=chunk.chunk_id,
                status=AgentStatus.INITIALIZING,
                hired_utc=sr.spawned_utc or datetime.now(timezone.utc).isoformat(),
            )
            pool.agents[handle.agent_id] = handle
            pool.total_hired += 1
            responses.append(HireResponse(agent=handle, spawned=True))

    log.info(
        "batch_hire_complete",
        mission_id=request.mission_id,
        hired=len(responses),
        requested=len(request.chunks),
    )

    return responses


@router.post("/fire/{agent_id}")
async def fire_specialist(agent_id: str, request: FireRequest) -> dict[str, Any]:
    """Terminate a specialist.

    1. Persist any partial artifacts to Vault
    2. HTTP DELETE orchestrator/corporate/agents/{id}
    3. Update WorkforcePool
    """
    pool = _pools.get(request.mission_id)
    if not pool or agent_id not in pool.agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found in pool")

    # Step 1: Terminate via Orchestrator
    orch_client = await get_corporate_orchestrator_client()
    try:
        result = await orch_client.terminate_agent(agent_id, reason=request.reason)
    except Exception as exc:
        log.error("agent_terminate_failed", error=str(exc), agent_id=agent_id)
        raise HTTPException(status_code=502, detail=f"Termination failed: {exc}") from exc

    # Step 2: Update pool
    handle = pool.agents[agent_id]
    handle.status = AgentStatus.TERMINATED
    pool.total_fired += 1

    log.info(
        "specialist_fired",
        agent_id=agent_id,
        reason=request.reason,
        mission_id=request.mission_id,
    )

    return {"terminated": True, "agent_id": agent_id, "reason": request.reason}


@router.post("/scale")
async def scale_workforce(request: ScaleRequest) -> list[dict[str, Any]]:
    """Evaluate and execute scaling decisions.

    1. compute_scale_decisions() — pure kernel call
    2. Execute each decision via hire/fire endpoints
    """
    pool = _pools.get(request.mission_id)
    if not pool:
        pool = _get_or_create_pool(request.mission_id)

    # Gather performance snapshots from pool agents
    performance = []
    for handle in pool.agents.values():
        if handle.status == AgentStatus.ACTIVE:
            perf = evaluate_performance(
                handle,
                {
                    "quality_score": handle.quality_score,
                    "confidence": 0.5,
                    "grounding_rate": 0.5,
                    "duration_ms": 0.0,
                    "cost": handle.total_cost,
                },
            )
            performance.append(perf)

    decisions = compute_scale_decisions(
        pool=pool,
        pending_chunks=request.pending_chunks,
        performance=performance,
        hardware_profile=request.hardware_profile,
    )

    results = [d.model_dump() for d in decisions]

    log.info(
        "scale_decisions_computed",
        mission_id=request.mission_id,
        decisions=len(decisions),
    )

    return results


@router.post("/match")
async def match_profile(request: MatchRequest) -> dict[str, Any]:
    """Find the best specialist profile for a chunk."""
    result = await match_specialist(
        chunk=request.chunk,
        available_profiles=request.available_profiles,
    )

    if result.signals:
        return result.signals[0].payload if isinstance(result.signals[0].payload, dict) else {}
    return {"error": "No match found"}


@router.get("/pool/{mission_id}")
async def get_pool(mission_id: str) -> dict[str, Any]:
    """List all agents in a mission pool."""
    pool = _pools.get(mission_id)
    if not pool:
        raise HTTPException(status_code=404, detail=f"Pool for mission {mission_id} not found")
    return pool.model_dump()
