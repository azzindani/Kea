"""
Quality Router — /quality/* endpoints.

HTTP endpoints for quality assessment, conflict detection/resolution,
and sprint auditing.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from shared.config import get_settings
from shared.logging.main import get_logger

from kernel.quality_resolver import (
    Conflict,
    QualityAudit,
    Resolution,
    detect_conflicts,
    resolve_conflict,
    score_sprint_quality,
)

from services.corporate_ops.clients.vault_ledger import (
    get_vault_ledger_client,
)

log = get_logger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class ConflictScanRequest(BaseModel):
    """Request to scan for artifact conflicts."""

    mission_id: str
    sprint_id: str | None = None
    artifacts: list[dict[str, Any]] | None = Field(
        default=None,
        description="Optional explicit artifact list; if omitted, fetches from Vault",
    )


class ConflictResolveRequest(BaseModel):
    """Request to resolve a conflict."""

    conflict: Conflict
    artifact_a: dict[str, Any]
    artifact_b: dict[str, Any]


class SprintAuditRequest(BaseModel):
    """Request to audit a sprint's quality."""

    sprint_id: str
    agent_results: list[dict[str, Any]]


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/conflicts/scan")
async def scan_for_conflicts(request: ConflictScanRequest) -> dict[str, Any]:
    """Scan artifacts for contradictions.

    1. Fetch artifacts from Vault (or use provided list)
    2. detect_conflicts() — pure kernel call
    3. Return detected conflicts
    """
    artifacts = request.artifacts

    if artifacts is None:
        # Fetch from Vault
        vault_client = await get_vault_ledger_client()
        try:
            vault_artifacts = await vault_client.read_artifacts(
                team_id=request.mission_id,
            )
            artifacts = [a.model_dump() for a in vault_artifacts]
        except Exception as exc:
            log.error("vault_read_failed", error=str(exc))
            raise HTTPException(
                status_code=502,
                detail=f"Failed to read artifacts from Vault: {exc}",
            ) from exc

    result = await detect_conflicts(artifacts=artifacts)

    if result.signals:
        return result.signals[0].payload if isinstance(result.signals[0].payload, dict) else {}
    return {"conflicts": [], "count": 0}


@router.post("/conflicts/resolve")
async def resolve_artifact_conflict(
    request: ConflictResolveRequest,
) -> dict[str, Any]:
    """Resolve a detected conflict.

    1. resolve_conflict() — pure kernel call
    2. Return resolution
    """
    result = await resolve_conflict(
        conflict=request.conflict,
        artifact_a=request.artifact_a,
        artifact_b=request.artifact_b,
    )

    if result.signals:
        return result.signals[0].payload if isinstance(result.signals[0].payload, dict) else {}
    return {"error": "Resolution failed"}


@router.post("/audit/sprint")
async def audit_sprint(request: SprintAuditRequest) -> dict[str, Any]:
    """Audit a sprint's quality from agent results.

    1. score_sprint_quality() — pure kernel call
    2. Return QualityAudit
    """
    result = await score_sprint_quality(
        agent_results=request.agent_results,
        sprint_id=request.sprint_id,
    )

    if result.signals:
        return result.signals[0].payload if isinstance(result.signals[0].payload, dict) else {}
    return {"error": "Audit failed"}


@router.get("/audit/mission/{mission_id}")
async def audit_mission(mission_id: str) -> dict[str, Any]:
    """Get a full quality report for a mission.

    Fetches all artifacts from Vault and runs aggregate quality analysis.
    """
    vault_client = await get_vault_ledger_client()

    try:
        artifacts = await vault_client.read_artifacts(team_id=mission_id)
    except Exception as exc:
        log.error("vault_read_failed", error=str(exc))
        raise HTTPException(
            status_code=502,
            detail=f"Failed to read artifacts: {exc}",
        ) from exc

    # Detect conflicts
    conflict_result = await detect_conflicts(
        artifacts=[a.model_dump() for a in artifacts]
    )

    conflicts_count = 0
    if conflict_result.signals:
        cd = conflict_result.signals[0].payload
        if isinstance(cd, dict):
            conflicts_count = cd.get("count", 0)

    return {
        "mission_id": mission_id,
        "total_artifacts": len(artifacts),
        "conflicts_found": conflicts_count,
        "status": "audit_complete",
    }
