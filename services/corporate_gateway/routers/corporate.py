"""
Corporate Router — THE Entry Point for the Corporation Kernel.

Implements ``POST /corporate/process`` — the ONE AND ONLY entry point.
All client interactions flow through this endpoint, regardless of
whether they trigger a full mission (NEW_TASK) or a memory recall
(FOLLOW_UP).

Orchestrates three phases:
  Phase 1 — CORPORATE GATE-IN:   Pure kernel + Vault HTTP
  Phase 2 — CORPORATE EXECUTE:   HTTP delegation to Corporate Ops :8011
  Phase 3 — CORPORATE GATE-OUT:  Vault HTTP + Pure kernel quality chain
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from shared.config import get_settings
from shared.inference_kit import InferenceKit
from shared.logging.main import get_logger
from shared.schemas import (
    CorporateProcessRequest,
    CorporateProcessResponse,
    MissionStatusResponse,
)

from services.corporate_gateway.clients.corporate_ops import get_corporate_ops_client
from services.corporate_gateway.clients.vault_ledger import (
    get_vault_client,
    VaultSession,
)

log = get_logger(__name__)

router = APIRouter()

# In-memory mission tracking (production: persist to Vault)
_ACTIVE_MISSIONS: dict[str, dict[str, Any]] = {}


# ============================================================================
# Phase 1: CORPORATE GATE-IN
# ============================================================================


async def _corporate_gate_in(
    request: CorporateProcessRequest,
    kit: InferenceKit,
) -> CorporateGateInResult:
    """Phase 1 — classify intent, assess strategy, decompose objective."""
    from kernel.corporate_gateway.engine import classify_intent, assess_strategy
    from kernel.corporate_gateway.types import (
        ClientIntent, CorporateGateInResult, SessionState,
    )
    from kernel.task_decomposition import decompose_goal
    from kernel.workforce_manager import MissionChunk
    start = time.perf_counter()
    settings = get_settings()
    vault = await get_vault_client()

    # 1. Load session context from Vault
    session: SessionState | None = None
    if request.session_id or request.client_id:
        vault_session = await vault.load_session(
            session_id=request.session_id,
            client_id=request.client_id,
        )
        if vault_session:
            session = SessionState(
                session_id=vault_session.session_id,
                client_id=vault_session.client_id,
                turns=vault_session.turns,
                active_mission_id=vault_session.active_mission_id,
                history_artifact_ids=vault_session.history_artifact_ids,
                last_intent=vault_session.last_intent,
                created_utc=vault_session.created_utc,
                updated_utc=vault_session.updated_utc,
            )

    # 2. Classify intent
    intent = await classify_intent(request.content, session, kit)
    log.info("gate_in_intent", intent=intent.value,
             session_exists=session is not None)

    # 3. Fast-path: STATUS_CHECK — no execution needed
    if intent == ClientIntent.STATUS_CHECK and session and session.active_mission_id:
        return CorporateGateInResult(
            request_id=request.request_id,
            session=session,
            intent=intent,
            fast_path_response={"type": "status_check",
                                "mission_id": session.active_mission_id},
            gate_in_duration_ms=(time.perf_counter() - start) * 1000,
        )

    # 4. Fast-path: FOLLOW_UP — memory recall, no execution
    if intent == ClientIntent.FOLLOW_UP and session:
        recalled = await vault.recall_memory(
            client_id=session.client_id,
            query=request.content,
        )
        recalled_dicts = [a.model_dump() for a in recalled]
        return CorporateGateInResult(
            request_id=request.request_id,
            session=session,
            intent=intent,
            fast_path_response={"type": "follow_up",
                                "recalled_artifacts": recalled_dicts},
            gate_in_duration_ms=(time.perf_counter() - start) * 1000,
        )

    # 5. Full pipeline: assess strategy
    strategy = await assess_strategy(request.content, session, kit)

    # 6. Decompose objective into MissionChunks
    chunks: list[dict[str, Any]] = []
    if intent not in (ClientIntent.CONVERSATION,):
        decompose_result = await decompose_goal(request.content, kit)
        subtasks: list[dict[str, Any]] = []
        if decompose_result.signals:
            payload = decompose_result.signals[0].payload
            if isinstance(payload, dict):
                subtasks = payload.get("sub_tasks", [])

        if not subtasks:
            subtasks = [{
                "item_id": f"chunk_{uuid.uuid4().hex[:8]}",
                "description": request.content,
                "dependencies": [],
                "priority": 0,
                "required_capabilities": ["general"],
            }]

        budget = request.budget_limit or 10.0
        for i, st in enumerate(subtasks):
            chunk = MissionChunk(
                chunk_id=st.get("item_id", f"chunk_{i}"),
                parent_objective_id=request.request_id,
                domain="general",
                sub_objective=st.get("description", request.content),
                required_skills=st.get("required_capabilities", []),
                required_tools=[],
                depends_on=st.get("dependencies", []),
                sprint_number=0,
                priority=st.get("priority", 0),
                token_budget=0,
                cost_budget=budget / max(1, len(subtasks)),
                time_budget_ms=60000.0,
                is_parallelizable=True,
                predecessor_artifact_ids=[],
            )
            chunks.append(chunk.model_dump())
    else:
        # CONVERSATION: single conversational chunk
        chunks = [MissionChunk(
            chunk_id=f"conv_{uuid.uuid4().hex[:8]}",
            parent_objective_id=request.request_id,
            domain="conversation",
            sub_objective=request.content,
            required_skills=["general"],
            required_tools=[],
            depends_on=[],
            sprint_number=1,
            priority=0,
            token_budget=0,
            cost_budget=request.budget_limit or 1.0,
            time_budget_ms=30000.0,
            is_parallelizable=False,
            predecessor_artifact_ids=[],
        ).model_dump()]

    # 7. Check for resumable checkpoint (for REVISION / resumed missions)
    checkpoint: dict[str, Any] | None = None
    if intent == ClientIntent.REVISION and session and session.active_mission_id:
        checkpoint = {"mission_id": session.active_mission_id,
                      "resume": True}

    duration = (time.perf_counter() - start) * 1000
    log.info("gate_in_complete", duration_ms=duration,
             intent=intent.value, chunks=len(chunks))

    return CorporateGateInResult(
        request_id=request.request_id,
        session=session,
        intent=intent,
        strategy=strategy,
        chunks=chunks,
        checkpoint=checkpoint,
        gate_in_duration_ms=duration,
    )


# ============================================================================
# Phase 2: CORPORATE EXECUTE
# ============================================================================


async def _corporate_execute(
    gate_in: CorporateGateInResult,
    request: CorporateProcessRequest,
) -> CorporateExecuteResult:
    """Phase 2 — delegate to Corporate Ops via HTTP."""
    from kernel.corporate_gateway.engine import handle_interrupt_logic
    from kernel.corporate_gateway.types import ClientIntent, CorporateExecuteResult
    start = time.perf_counter()
    settings = get_settings()
    co_client = await get_corporate_ops_client()

    # Fast-path: STATUS_CHECK
    if gate_in.fast_path_response and gate_in.fast_path_response.get("type") == "status_check":
        mission_id = gate_in.fast_path_response["mission_id"]
        try:
            status = await co_client.get_mission_status(mission_id)
            status_report = (
                f"Mission {mission_id}: "
                f"Sprint {status.get('current_sprint', '?')} of {status.get('total_sprints', '?')}, "
                f"{status.get('completion_pct', 0) * 100:.0f}% complete"
            )
        except Exception:
            status_report = f"Mission {mission_id}: Unable to retrieve status."

        return CorporateExecuteResult(
            mission_id=mission_id,
            status_report=status_report,
            execute_duration_ms=(time.perf_counter() - start) * 1000,
        )

    # Fast-path: FOLLOW_UP — no execution
    if gate_in.fast_path_response and gate_in.fast_path_response.get("type") == "follow_up":
        return CorporateExecuteResult(
            execute_duration_ms=(time.perf_counter() - start) * 1000,
        )

    # Fast-path: INTERRUPT
    if gate_in.intent == ClientIntent.INTERRUPT:
        mission_id = (gate_in.session.active_mission_id
                      if gate_in.session else None)
        if mission_id:
            interrupt = handle_interrupt_logic(
                request.content, mission_id
            )
            if interrupt.interrupt_type == "abort":
                result = await co_client.abort_mission(mission_id)
            else:
                result = await co_client.send_interrupt(
                    mission_id, interrupt.model_dump()
                )
            return CorporateExecuteResult(
                mission_id=mission_id,
                mission_result=result,
                interrupts_handled=1,
                execute_duration_ms=(time.perf_counter() - start) * 1000,
            )
        return CorporateExecuteResult(
            status_report="No active mission to interrupt.",
            execute_duration_ms=(time.perf_counter() - start) * 1000,
        )

    # Full execution: dispatch to Corporate Ops
    mission_id = f"mission_{uuid.uuid4().hex[:8]}"
    mission_payload: dict[str, Any] = {
        "mission_id": mission_id,
        "objective": request.content,
        "chunks": gate_in.chunks or [],
        "budget": request.budget_limit or 10.0,
        "available_profiles": [],
    }

    if gate_in.strategy:
        mission_payload["strategy"] = gate_in.strategy.model_dump()

    # Checkpoint resume
    if gate_in.checkpoint and gate_in.checkpoint.get("resume"):
        existing_id = gate_in.checkpoint["mission_id"]
        try:
            result = await co_client.resume_mission(existing_id)
            return CorporateExecuteResult(
                mission_id=existing_id,
                mission_result=result,
                execute_duration_ms=(time.perf_counter() - start) * 1000,
            )
        except Exception as exc:
            log.warning("resume_failed_starting_fresh", error=str(exc))

    # Dispatch
    log.info("execute_dispatching", mission_id=mission_id,
             chunks=len(gate_in.chunks or []))

    mission_result = await co_client.start_mission(mission_data=mission_payload)

    # Track
    _ACTIVE_MISSIONS[mission_id] = {
        "status": "running",
        "request_id": request.request_id,
        "result": mission_result,
    }

    # If the Corporate Ops returns synchronously (small missions), we're done.
    # For async missions, the client can poll via /corporate/missions/{id}/status.

    duration = (time.perf_counter() - start) * 1000
    log.info("execute_complete", mission_id=mission_id,
             duration_ms=duration)

    return CorporateExecuteResult(
        mission_id=mission_id,
        mission_result=mission_result,
        execute_duration_ms=duration,
    )


# ============================================================================
# Phase 3: CORPORATE GATE-OUT
# ============================================================================


async def _corporate_gate_out(
    gate_in: CorporateGateInResult,
    execute: CorporateExecuteResult,
    request: CorporateProcessRequest,
    kit: InferenceKit,
) -> CorporateProcessResponse:
    """Phase 3 — collect artifacts, quality chain, synthesize, persist."""
    from kernel.corporate_gateway.engine import synthesize_response
    start = time.perf_counter()
    settings = get_settings()
    vault = await get_vault_client()
    co_client = await get_corporate_ops_client()

    session_id = request.session_id or f"session_{uuid.uuid4().hex[:8]}"
    result_id = f"result_{uuid.uuid4().hex[:8]}"

    # --- Fast-path responses ---

    # STATUS_CHECK
    if execute.status_report and not execute.mission_result:
        gate_out_ms = (time.perf_counter() - start) * 1000
        return CorporateProcessResponse(
            result_id=result_id,
            trace_id=request.trace_id,
            request_id=request.request_id,
            session_id=session_id,
            intent=gate_in.intent.value,
            response_title="Mission Status",
            response_summary=execute.status_report,
            response_content=execute.status_report,
            quality_score=1.0,
            confidence=1.0,
            grounding_score=1.0,
            completeness_pct=1.0,
            gate_in_ms=gate_in.gate_in_duration_ms,
            execute_ms=execute.execute_duration_ms,
            gate_out_ms=gate_out_ms,
            total_duration_ms=(
                gate_in.gate_in_duration_ms
                + execute.execute_duration_ms
                + gate_out_ms
            ),
        )

    # FOLLOW_UP
    if gate_in.fast_path_response and gate_in.fast_path_response.get("type") == "follow_up":
        recalled = gate_in.fast_path_response.get("recalled_artifacts", [])
        content = "\n\n".join(
            a.get("content", "") for a in recalled
        ) if recalled else "No matching records found."
        title = "Recalled Information"
        summary = content[:500] + ("..." if len(content) > 500 else "")

        gate_out_ms = (time.perf_counter() - start) * 1000
        return CorporateProcessResponse(
            result_id=result_id,
            trace_id=request.trace_id,
            request_id=request.request_id,
            session_id=session_id,
            intent=gate_in.intent.value,
            response_title=title,
            response_summary=summary,
            response_content=content,
            quality_score=0.9,
            confidence=0.85,
            grounding_score=1.0,
            completeness_pct=1.0,
            gate_in_ms=gate_in.gate_in_duration_ms,
            execute_ms=execute.execute_duration_ms,
            gate_out_ms=gate_out_ms,
            total_duration_ms=(
                gate_in.gate_in_duration_ms
                + execute.execute_duration_ms
                + gate_out_ms
            ),
        )

    # --- Full Gate-Out pipeline ---

    mission_id = execute.mission_id or ""
    mission_result = execute.mission_result or {}

    # 1. Collect artifacts from Vault
    artifacts: list[dict[str, Any]] = []
    if mission_id:
        vault_artifacts = await vault.collect_artifacts(mission_id)
        artifacts = [a.model_dump() for a in vault_artifacts]

    # Fall back to inline mission result if Vault returned nothing
    if not artifacts and mission_result:
        artifacts = [{"content": str(mission_result),
                      "metadata": {"topic": "Mission Result"}}]

    # 2. Quality audit via Corporate Ops
    quality_report: dict[str, Any] = {}
    if mission_id:
        quality_report = await co_client.audit_mission(mission_id)

    # 3. Synthesize response (pure kernel)
    strategy = gate_in.strategy
    if not strategy:
        from kernel.corporate_gateway.types import StrategyAssessment, ScalingMode
        strategy = StrategyAssessment(scaling_mode=ScalingMode.SOLO)

    synth = await synthesize_response(
        artifacts=artifacts,
        strategy=strategy,
        quality_report=quality_report,
        kit=kit,
    )

    # 4. Quality metrics
    overall_quality = quality_report.get("overall_score", 0.8)
    confidence_avg = (
        sum(synth.confidence_map.values()) / max(1, len(synth.confidence_map))
        if synth.confidence_map else 0.8
    )

    # 5. Mission summary
    total_agents = mission_result.get("total_agents_hired", len(synth.source_agents))
    total_cost = mission_result.get("total_cost", 0.0)

    # 6. Persist session + result to Vault
    session_data = VaultSession(
        session_id=session_id,
        client_id=request.client_id,
        turns=(gate_in.session.turns + 1) if gate_in.session else 1,
        active_mission_id=None,
        last_intent=gate_in.intent.value,
    )
    try:
        await vault.persist_session(session_data)
    except Exception as exc:
        log.warning("session_persist_failed", error=str(exc))

    if mission_id:
        try:
            await vault.persist_result(
                mission_id=mission_id,
                result_data={
                    "title": synth.title,
                    "summary": synth.executive_summary,
                    "content": synth.full_content,
                    "client_id": request.client_id,
                    "quality_score": overall_quality,
                },
            )
        except Exception as exc:
            log.warning("result_persist_failed", error=str(exc))

        try:
            await vault.write_audit_log(
                mission_id=mission_id,
                event_type="corporate_process_complete",
                details={
                    "request_id": request.request_id,
                    "intent": gate_in.intent.value,
                    "agents": total_agents,
                    "cost": total_cost,
                },
            )
        except Exception as exc:
            log.warning("audit_log_failed", error=str(exc))

    # Clean up tracking
    _ACTIVE_MISSIONS.pop(mission_id, None)

    gate_out_ms = (time.perf_counter() - start) * 1000

    return CorporateProcessResponse(
        result_id=result_id,
        trace_id=request.trace_id,
        request_id=request.request_id,
        session_id=session_id,
        intent=gate_in.intent.value,
        response_title=synth.title,
        response_summary=synth.executive_summary,
        response_content=synth.full_content,
        quality_score=overall_quality,
        confidence=confidence_avg,
        grounding_score=quality_report.get("grounding_score", 0.85),
        completeness_pct=1.0 - (len(synth.gaps) * 0.1),
        is_partial=synth.is_partial,
        total_agents_hired=total_agents,
        total_agents_fired=total_agents,
        total_cost=total_cost,
        total_duration_ms=(
            gate_in.gate_in_duration_ms
            + execute.execute_duration_ms
            + gate_out_ms
        ),
        gate_in_ms=gate_in.gate_in_duration_ms,
        execute_ms=execute.execute_duration_ms,
        gate_out_ms=gate_out_ms,
    )


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/process", response_model=CorporateProcessResponse)
async def corporate_process(
    request: CorporateProcessRequest,
) -> CorporateProcessResponse:
    """THE entry point for the Corporation Kernel.

    All client interactions flow through this single endpoint.
    Orchestrates: Gate-In → Execute → Gate-Out.
    """
    log.info("corporate_process_started",
             request_id=request.request_id,
             client_id=request.client_id,
             trace_id=request.trace_id)

    kit = InferenceKit()

    # Phase 1
    gate_in = await _corporate_gate_in(request, kit)

    # Phase 2
    execute = await _corporate_execute(gate_in, request)

    # Phase 3
    response = await _corporate_gate_out(gate_in, execute, request, kit)

    log.info("corporate_process_complete",
             request_id=request.request_id,
             intent=response.intent,
             duration_ms=response.total_duration_ms)

    return response


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> dict[str, Any]:
    """Get session state from Vault."""
    vault = await get_vault_client()
    session = await vault.load_session(session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.model_dump()


@router.get("/missions/{mission_id}/status",
            response_model=MissionStatusResponse)
async def get_mission_status(mission_id: str) -> MissionStatusResponse:
    """Get active mission status (proxies to Corporate Ops)."""
    co_client = await get_corporate_ops_client()
    try:
        status = await co_client.get_mission_status(mission_id)
        return MissionStatusResponse(
            mission_id=mission_id,
            status=status.get("status", "unknown"),
            completion_pct=status.get("completion_pct", 0.0),
            current_sprint=status.get("current_sprint", 0),
            total_sprints=status.get("total_sprints", 0),
            active_agents=status.get("active_agents", 0),
            elapsed_ms=status.get("elapsed_ms", 0.0),
            estimated_remaining_ms=status.get("estimated_remaining_ms", 0.0),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Corporate Ops unavailable: {exc}")


@router.post("/missions/{mission_id}/interrupt")
async def send_interrupt(mission_id: str, content: str = "") -> dict[str, Any]:
    """Forward a client interrupt to Corporate Ops."""
    interrupt = handle_interrupt_logic(content, mission_id)

    co_client = await get_corporate_ops_client()
    if interrupt.interrupt_type == "abort":
        result = await co_client.abort_mission(mission_id)
    else:
        result = await co_client.send_interrupt(
            mission_id, interrupt.model_dump()
        )

    return {
        "interrupt_type": interrupt.interrupt_type,
        "confidence": interrupt.confidence,
        "result": result,
    }


@router.get("/history/{client_id}")
async def get_client_history(client_id: str) -> list[dict[str, Any]]:
    """Search client interaction history from Vault."""
    vault = await get_vault_client()
    history = await vault.get_client_history(client_id)
    return [a.model_dump() for a in history]
