"""
Swarm Manager Service — Governance, Compliance & Resource Gating (Port 8005).

Routes:
  GET  /health
  POST /compliance/check
  POST /kill-switch/activate
  DELETE /kill-switch              Resume from emergency stop
  GET  /kill-switch/status
  POST /kill-switch/blacklist/{tool}
  DELETE /kill-switch/blacklist/{tool}
  GET  /agents                     List supervised escalations
  POST /agents/{work_id}/escalate  Escalate a work item
  POST /agents/{work_id}/resolve   Resolve a pending escalation
  GET  /rate-limits/{agent_id}     Check rate limit remaining for an agent
  GET  /resource/status            Current resource governor state
"""

from __future__ import annotations

from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from services.swarm_manager.core.compliance import ComplianceStandard, get_compliance_engine
from services.swarm_manager.core.guards import get_resource_guard
from services.swarm_manager.core.kill_switch import get_kill_switch
from services.swarm_manager.core.supervisor import get_supervisor
from shared.logging import get_logger

logger = get_logger(__name__)

app = FastAPI(title="Swarm Manager")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "swarm_manager"}


# ============================================================================
# Compliance
# ============================================================================


class ComplianceCheckRequest(BaseModel):
    operation: str
    context: dict[str, Any]
    standards: list[str] | None = None


@app.post("/compliance/check")
async def check_compliance(request: ComplianceCheckRequest) -> dict:
    """Check operation against compliance standards."""
    engine = get_compliance_engine()
    standards = None
    if request.standards:
        standards = []
        for s in request.standards:
            try:
                standards.append(ComplianceStandard(s))
            except ValueError:
                try:
                    standards.append(ComplianceStandard(s.lower()))
                except ValueError:
                    continue

    report = await engine.check_operation(
        operation=request.operation,
        context=request.context,
        standards=standards,
    )
    return {
        "passed": report.passed,
        "summary": report.summary,
        "issues": [
            {
                "check_id": i.check_id,
                "severity": i.severity.value,
                "message": i.message,
                "details": i.details,
            }
            for i in report.issues
        ],
        "checks_passed": report.checks_passed,
        "checks_failed": report.checks_failed,
        "checks_warned": report.checks_warned,
    }


# ============================================================================
# Kill Switch
# ============================================================================


class EmergencyStopRequest(BaseModel):
    reason: str


class BlacklistRequest(BaseModel):
    reason: str = "Manual blacklist"
    duration_minutes: int = 30


@app.post("/kill-switch/activate", status_code=200)
async def activate_kill_switch(request: EmergencyStopRequest) -> dict:
    """Trigger an emergency stop of all agents."""
    switch = get_kill_switch()
    await switch.emergency_stop(request.reason)
    logger.critical(f"Kill switch activated: {request.reason}")
    return {"activated": True, "reason": request.reason}


@app.delete("/kill-switch", status_code=200)
async def resume_from_emergency() -> dict:
    """Resume operations after an emergency stop."""
    switch = get_kill_switch()
    await switch.resume()
    return {"resumed": True}


@app.get("/kill-switch/status")
async def kill_switch_status() -> dict:
    """Return current kill switch state."""
    switch = get_kill_switch()
    return {
        "emergency_stopped": switch.is_emergency_stopped,
        "stop_reason": switch._stop_reason,
        "blacklisted_tools": list(switch._blacklisted_tools.keys()),
        "paused_departments": list(switch._paused_departments),
    }


@app.post("/kill-switch/blacklist/{tool_name}", status_code=201)
async def blacklist_tool(tool_name: str, request: BlacklistRequest) -> dict:
    """Temporarily blacklist a tool."""
    switch = get_kill_switch()
    switch.blacklist_tool(
        tool_name, reason=request.reason, duration_minutes=request.duration_minutes
    )
    return {"tool": tool_name, "blacklisted": True, "duration_minutes": request.duration_minutes}


@app.delete("/kill-switch/blacklist/{tool_name}", status_code=200)
async def unblacklist_tool(tool_name: str) -> dict:
    """Remove a tool from the blacklist."""
    switch = get_kill_switch()
    switch.unblacklist_tool(tool_name)
    return {"tool": tool_name, "blacklisted": False}


# ============================================================================
# Supervisor (agent oversight)
# ============================================================================


class EscalateRequest(BaseModel):
    escalation_type: str = "error"
    context: dict[str, Any] = {}


@app.get("/agents")
async def list_agent_escalations() -> dict:
    """List pending escalations from the supervisor."""
    supervisor = get_supervisor()
    count = supervisor.pending_escalation_count()
    escalations = (
        list(supervisor._pending_escalations.values())
        if hasattr(supervisor, "_pending_escalations")
        else []
    )
    return {
        "pending_count": count,
        "escalations": [
            {
                "escalation_id": e.escalation_id if hasattr(e, "escalation_id") else str(i),
                "type": e.escalation_type.value if hasattr(e, "escalation_type") else "unknown",
                "created_at": e.created_at.isoformat() if hasattr(e, "created_at") else None,
            }
            for i, e in enumerate(escalations)
        ],
    }


@app.post("/agents/{work_id}/resolve", status_code=200)
async def resolve_agent_escalation(work_id: str, resolution: str = "resolved") -> dict:
    """Resolve a pending escalation for a work item."""
    supervisor = get_supervisor()
    try:
        await supervisor.resolve_escalation(work_id, resolution)
        return {"work_id": work_id, "resolved": True, "resolution": resolution}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Resource Guard
# ============================================================================


@app.get("/rate-limits/{agent_id}")
async def get_rate_limit(agent_id: str) -> dict:
    """Check remaining rate limit calls for an agent."""
    guard = get_resource_guard()
    remaining = (
        guard._rate_limiter.get_remaining(agent_id) if hasattr(guard, "_rate_limiter") else -1
    )
    can_spawn = await guard.check_can_spawn(session_id=agent_id)
    return {"agent_id": agent_id, "can_spawn": can_spawn, "rate_limit_remaining": remaining}


@app.get("/resource/status")
async def resource_status() -> dict:
    """Return current resource governor health state."""
    from services.swarm_manager.core.resource_governor import get_governor

    governor = get_governor()
    state = await governor.get_system_state()
    return {
        "state": state.value if hasattr(state, "value") else str(state),
        "active_agents": governor._active_agents,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)
