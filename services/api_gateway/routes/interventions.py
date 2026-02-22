"""
HITL (Human-in-the-Loop) API Routes.

Endpoints for human intervention and approval workflows.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from shared.database.connection import get_database_pool
from shared.logging.main import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ============================================================================
# Models
# ============================================================================


class InterventionType(StrEnum):
    """Types of intervention requests."""

    APPROVAL = "approval"
    REVIEW = "review"
    CLARIFICATION = "clarification"
    CORRECTION = "correction"


class InterventionStatus(StrEnum):
    """Intervention status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


class InterventionRequest(BaseModel):
    """Intervention request from the system."""

    intervention_id: str
    job_id: str
    type: InterventionType
    message: str
    context: dict[str, Any] = {}
    options: list[str] = []
    status: InterventionStatus = InterventionStatus.PENDING
    created_at: datetime
    responded_at: datetime | None = None


class CreateInterventionRequest(BaseModel):
    """Create intervention request."""

    job_id: str
    type: InterventionType
    message: str
    context: dict[str, Any] = {}
    options: list[str] = []


class InterventionResponse(BaseModel):
    """Human response to intervention."""

    decision: str  # approved, rejected, or option value
    feedback: str = ""
    modifications: dict[str, Any] = {}


async def _db_insert(row: dict) -> None:
    pool = await get_database_pool()
    await pool.execute(
        """
        INSERT INTO human_interventions
            (intervention_id, job_id, type, message, context, options, status, response, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (intervention_id) DO NOTHING
        """,
        row["intervention_id"],
        row["job_id"],
        str(row["type"].value if hasattr(row["type"], "value") else row["type"]),
        row["message"],
        json.dumps(row["context"]),
        json.dumps(row["options"]),
        str(row["status"].value if hasattr(row["status"], "value") else row["status"]),
        None,
        row["created_at"],
    )


async def _db_update(
    intervention_id: str, status: str, response: dict, responded_at: datetime
) -> None:
    pool = await get_database_pool()
    await pool.execute(
        """
        UPDATE human_interventions
        SET status = $1, response = $2, responded_at = $3
        WHERE intervention_id = $4
        """,
        status,
        json.dumps(response),
        responded_at,
        intervention_id,
    )


async def _db_fetch(intervention_id: str) -> dict | None:
    pool = await get_database_pool()
    row = await pool.fetchrow(
        "SELECT * FROM human_interventions WHERE intervention_id = $1", intervention_id
    )
    return _row_to_dict(row) if row else None


async def _db_list(job_id: str | None, status: str | None, limit: int) -> list[dict]:
    pool = await get_database_pool()
    conditions = []
    params: list = []
    idx = 1
    if job_id:
        conditions.append(f"job_id = ${idx}")
        params.append(job_id)
        idx += 1
    if status:
        conditions.append(f"status = ${idx}")
        params.append(status)
        idx += 1
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)
    rows = await pool.fetch(
        f"SELECT * FROM human_interventions {where} ORDER BY created_at DESC LIMIT ${idx}",
        *params,
    )
    return [_row_to_dict(r) for r in rows]


def _row_to_dict(row: Any) -> dict:
    r = dict(row)
    r["context"] = (
        json.loads(r["context"]) if isinstance(r["context"], str) else (r["context"] or {})
    )
    r["options"] = (
        json.loads(r["options"]) if isinstance(r["options"], str) else (r["options"] or [])
    )
    r["response"] = json.loads(r["response"]) if r.get("response") else None
    return r


# ============================================================================
# Routes
# ============================================================================


@router.post("/", response_model=InterventionRequest)
async def create_intervention(request: CreateInterventionRequest) -> Any:
    """Create a new intervention request (persisted to PostgreSQL)."""
    intervention_id = f"int-{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow()
    row = {
        "intervention_id": intervention_id,
        "job_id": request.job_id,
        "type": request.type,
        "message": request.message,
        "context": request.context,
        "options": request.options,
        "status": InterventionStatus.PENDING,
        "created_at": now,
        "responded_at": None,
        "response": None,
    }
    try:
        await _db_insert(row)
    except Exception as e:
        logger.error(f"Failed to persist intervention: {e}")

    logger.info(f"Created intervention {intervention_id} for job {request.job_id}")
    return InterventionRequest(
        intervention_id=intervention_id,
        job_id=request.job_id,
        type=request.type,
        message=request.message,
        context=request.context,
        options=request.options,
        status=InterventionStatus.PENDING,
        created_at=now,
    )


# Route order matters — static paths before dynamic paths


@router.get("/pending")
async def list_pending_interventions() -> dict:
    """List all pending interventions requiring human action."""
    from shared.config import get_settings
    settings = get_settings()
    try:
        rows = await _db_list(job_id=None, status="pending", limit=settings.api.default_limit * 2)
        pending = [
            InterventionRequest(
                intervention_id=r["intervention_id"],
                job_id=r["job_id"],
                type=InterventionType(r["type"]),
                message=r["message"],
                context=r["context"],
                options=r["options"],
                status=InterventionStatus(r["status"]),
                created_at=r["created_at"],
                responded_at=r.get("responded_at"),
            )
            for r in rows
        ]
        return {"pending": pending, "count": len(pending)}
    except Exception as e:
        logger.warning(f"DB pending list failed: {e}")
        return {"pending": [], "count": 0}


@router.get("/{intervention_id}", response_model=InterventionRequest)
async def get_intervention(intervention_id: str) -> Any:
    """Get intervention details."""
    try:
        r = await _db_fetch(intervention_id)
    except Exception as e:
        logger.warning(f"DB fetch failed: {e}")
        r = None
    if r is None:
        raise HTTPException(
            status_code=get_settings().status_codes.not_found, 
            detail="Intervention not found"
        )
    return InterventionRequest(
        intervention_id=r["intervention_id"],
        job_id=r["job_id"],
        type=InterventionType(r["type"]),
        message=r["message"],
        context=r["context"],
        options=r["options"],
        status=InterventionStatus(r["status"]),
        created_at=r["created_at"],
        responded_at=r.get("responded_at"),
    )


@router.post("/{intervention_id}/respond")
async def respond_to_intervention(intervention_id: str, response: InterventionResponse) -> dict:
    """Submit human response to intervention."""
    try:
        r = await _db_fetch(intervention_id)
    except Exception as e:
        logger.warning(f"DB fetch failed: {e}")
        r = None
    if r is None:
        raise HTTPException(status_code=404, detail="Intervention not found")
    if r["status"] != "pending":
        raise HTTPException(
            status_code=get_settings().status_codes.bad_request, 
            detail="Intervention already responded to"
        )

    if response.decision == "approved":
        new_status = InterventionStatus.APPROVED
    elif response.decision == "rejected":
        new_status = InterventionStatus.REJECTED
    else:
        new_status = InterventionStatus.MODIFIED

    responded_at = datetime.utcnow()
    try:
        await _db_update(intervention_id, new_status.value, response.model_dump(), responded_at)
    except Exception as e:
        logger.error(f"Failed to persist response: {e}")

    logger.info(f"Intervention {intervention_id} responded: {response.decision}")
    return {
        "message": "Response recorded",
        "intervention_id": intervention_id,
        "status": new_status,
    }


@router.get("/")
async def list_interventions(
    job_id: str | None = None,
    status: InterventionStatus | None = None,
    limit: int = 50,
) -> dict:
    """List interventions with filtering."""
    status_str = status.value if status else None
    try:
        rows = await _db_list(job_id=job_id, status=status_str, limit=limit)
    except Exception as e:
        logger.warning(f"DB list failed: {e}")
        rows = []

    results = [
        InterventionRequest(
            intervention_id=r["intervention_id"],
            job_id=r["job_id"],
            type=InterventionType(r["type"]),
            message=r["message"],
            context=r["context"],
            options=r["options"],
            status=InterventionStatus(r["status"]),
            created_at=r["created_at"],
            responded_at=r.get("responded_at"),
        )
        for r in rows
    ]
    return {"interventions": results, "total": len(results)}
