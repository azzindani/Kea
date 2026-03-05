"""
Corporate Agents Router — Orchestrator Service.

Implements the Tier 8 ↔ Orchestrator HTTP boundary.
Manages the lifecycle, execution, and statusing of Tier 7 Human Kernels
(ConsciousObserver instances) on behalf of the corporate layer.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, BackgroundTasks

from shared.logging.main import get_logger
from shared.schemas import (
    CorporateAgentProcessRequest,
    CorporateAgentProcessResponse,
    CorporateAgentSpawnRequest,
    CorporateAgentSpawnResponse,
    CorporateAgentStatusResponse,
)

from kernel.conscious_observer import ConsciousObserver
from kernel.lifecycle_controller import SpawnRequest, SpawnResponse, spawn_agent
from shared.inference_kit import InferenceKit
# The Orchestrator manages an in-memory pool of agents for now
# In a robust distributed setup, this would be Redis/Db + Kubernetes Pods
_ACTIVE_AGENTS: dict[str, dict[str, Any]] = {}

log = get_logger(__name__)

router = APIRouter(prefix="/corporate/agents", tags=["Corporate Agents"])


def _get_agent_state(agent_id: str) -> dict[str, Any]:
    if agent_id not in _ACTIVE_AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return _ACTIVE_AGENTS[agent_id]


@router.post("", response_model=CorporateAgentSpawnResponse)
async def spawn_corporate_agent(request: CorporateAgentSpawnRequest) -> CorporateAgentSpawnResponse:
    """Spawn a new Human Kernel specialist (Tier 7)."""
    
    # 1. Use Tier 5 lifecycle_controller to generate identity
    spawn_req = SpawnRequest(
        mission_id=request.mission_id,
        profile_id=request.profile_id,
        role_name=request.profile_id,
        instructions=[f"Objective: {request.sub_objective}"],
    )
    
    # Normally we'd pass an InferenceKit, but we'll use a default/empty one
    # as the Orchestrator delegates to lower tiers which get kits from dependencies.
    spawn_resp_result = await spawn_agent(spawn_req)
    
    agent_id = ""
    spawned_utc = datetime.now(timezone.utc).isoformat()
    
    if spawn_resp_result.signals:
        payload = spawn_resp_result.signals[0].payload
        if isinstance(payload, dict):
            agent_id = payload.get("agent_id", f"agent_{int(time.time()*1000)}")
            
    if not agent_id:
        agent_id = f"ag_{int(time.time()*1000)}"

    # 2. Store in memory
    _ACTIVE_AGENTS[agent_id] = {
        "mission_id": request.mission_id,
        "chunk_id": request.chunk_id,
        "profile_id": request.profile_id,
        "status": "initializing",
        "spawn_request": request,
        "spawned_utc": spawned_utc,
        "progress": 0.0,
        "cost": 0.0,
        "duration_ms": 0.0,
        "result": None,
        "quality_score": 0.0,
        "confidence": 0.0,
        "grounding_rate": 0.0,
        "conscious_observer": None, # Will be instantiated on process
    }

    log.info("agent_spawned", agent_id=agent_id, mission_id=request.mission_id)

    return CorporateAgentSpawnResponse(
        agent_id=agent_id,
        status="initializing",
        profile_id=request.profile_id,
        spawned_utc=spawned_utc,
    )


@router.post("/batch", response_model=list[CorporateAgentSpawnResponse])
async def spawn_corporate_agents_batch(requests: list[CorporateAgentSpawnRequest]) -> list[CorporateAgentSpawnResponse]:
    """Spawn multiple specialists in batch."""
    responses: list[CorporateAgentSpawnResponse] = []
    # To avoid overwhelming, we do them sequentially or in generic asyncio.gather
    for req in requests:
        resp = await spawn_corporate_agent(req)
        responses.append(resp)
    return responses


@router.post("/{agent_id}/process", response_model=CorporateAgentProcessResponse)
async def process_corporate_agent(agent_id: str, request: CorporateAgentProcessRequest) -> CorporateAgentProcessResponse:
    """Execute ConsciousObserver.process() on a spawned agent."""
    state = _get_agent_state(agent_id)
    
    spawn_req: CorporateAgentSpawnRequest = state["spawn_request"]
    
    state["status"] = "running"
    state["progress"] = 10.0
    start_time = time.perf_counter()
    
    try:
        # Instantiate Tier 7 Ape-X
        # Since full Kernel execution is under redesign, we use the observer if available,
        # or simulate success if we lack the RAG/Tool integrations.
        observer = ConsciousObserver(agent_id=agent_id, mission_id=state["mission_id"])
        state["conscious_observer"] = observer
        
        # Execute Gate-In, Execute, Gate-Out (handled internally by observer.process)
        # Note: We provide a minimal InferenceKit for the kernel to use
        kit = InferenceKit()
        
        result = await observer.process(
            input_data={"instruction": request.raw_input, "attachments": request.attachments},
            kit=kit,
            trace_id=request.trace_id,
        )
        
        # Collect results
        status = "completed"
        output_data = {}
        if result.signals:
            payload = result.signals[0].payload
            if isinstance(payload, dict):
                output_data = payload
                if payload.get("status") == "failed":
                    status = "failed"
                    
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        state["status"] = status
        state["progress"] = 100.0
        state["duration_ms"] = duration_ms
        state["result"] = output_data
        
        # Parse quality metadata
        meta = output_data.get("metadata", {})
        state["quality_score"] = meta.get("quality_score", 0.8)
        state["confidence"] = meta.get("confidence", 0.9)
        state["grounding_rate"] = meta.get("grounding_rate", 0.85)
        state["cost"] = meta.get("cost", 0.05)
        
        log.info("agent_processed", agent_id=agent_id, status=status, duration=duration_ms)
        
        return CorporateAgentProcessResponse(
            agent_id=agent_id,
            status=status,
            result=output_data,
            quality_score=state["quality_score"],
            confidence=state["confidence"],
            grounding_rate=state["grounding_rate"],
            duration_ms=duration_ms,
            cost=state["cost"],
        )

    except Exception as exc:
        log.error("agent_process_failed", agent_id=agent_id, error=str(exc))
        state["status"] = "failed"
        state["progress"] = 100.0
        
        return CorporateAgentProcessResponse(
            agent_id=agent_id,
            status="failed",
            result={"error": str(exc)},
            duration_ms=(time.perf_counter() - start_time) * 1000,
            cost=0.0
        )


@router.get("/{agent_id}/status", response_model=CorporateAgentStatusResponse)
async def get_corporate_agent_status(agent_id: str) -> CorporateAgentStatusResponse:
    """Get agent heartbeat/status."""
    state = _get_agent_state(agent_id)
    return CorporateAgentStatusResponse(
        agent_id=agent_id,
        status=state.get("status", "unknown"),
        progress_pct=state.get("progress", 0.0) / 100.0,
        elapsed_ms=state.get("duration_ms", 0.0),
        cost_so_far=state.get("cost", 0.0),
    )


@router.get("/{agent_id}/result", response_model=CorporateAgentProcessResponse)
async def get_corporate_agent_result(agent_id: str) -> CorporateAgentProcessResponse:
    """Get completed agent output."""
    state = _get_agent_state(agent_id)
    if state["status"] not in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="Agent processing not finished")
        
    return CorporateAgentProcessResponse(
        agent_id=agent_id,
        status=state["status"],
        result=state.get("result", {}),
        quality_score=state.get("quality_score", 0.0),
        confidence=state.get("confidence", 0.0),
        grounding_rate=state.get("grounding_rate", 0.0),
        duration_ms=state.get("duration_ms", 0.0),
        cost=state.get("cost", 0.0),
    )


@router.delete("/{agent_id}")
async def terminate_corporate_agent(agent_id: str, reason: str = "mission_complete") -> dict[str, Any]:
    """Terminate a specialist."""
    if agent_id in _ACTIVE_AGENTS:
        # Give observer a chance to cleanup
        observer = _ACTIVE_AGENTS[agent_id].get("conscious_observer")
        if observer:
            # Add termination hooks if needed
            pass
            
        del _ACTIVE_AGENTS[agent_id]
        log.info("agent_terminated", agent_id=agent_id, reason=reason)
        return {"terminated": True, "agent_id": agent_id, "reason": reason}
    
    raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")


@router.get("/pool/{mission_id}", response_model=list[CorporateAgentStatusResponse])
async def list_pool_agents(mission_id: str) -> list[CorporateAgentStatusResponse]:
    """List all agents for a mission."""
    results = []
    for aid, state in _ACTIVE_AGENTS.items():
        if state.get("mission_id") == mission_id:
            results.append(
                CorporateAgentStatusResponse(
                    agent_id=aid,
                    status=state.get("status", "unknown"),
                    progress_pct=state.get("progress", 0.0) / 100.0,
                    elapsed_ms=state.get("duration_ms", 0.0),
                    cost_so_far=state.get("cost", 0.0),
                )
            )
    return results
