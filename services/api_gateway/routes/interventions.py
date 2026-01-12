"""
HITL (Human-in-the-Loop) API Routes.

Endpoints for human intervention and approval workflows.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from shared.logging import get_logger


logger = get_logger(__name__)

router = APIRouter()


# ============================================================================
# Models
# ============================================================================

class InterventionType(str, Enum):
    """Types of intervention requests."""
    APPROVAL = "approval"
    REVIEW = "review"
    CLARIFICATION = "clarification"
    CORRECTION = "correction"


class InterventionStatus(str, Enum):
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


# In-memory store
_interventions: dict[str, dict] = {}


# ============================================================================
# Routes
# ============================================================================

@router.post("/", response_model=InterventionRequest)
async def create_intervention(request: CreateInterventionRequest):
    """Create a new intervention request."""
    import uuid
    
    intervention_id = f"int-{uuid.uuid4().hex[:12]}"
    
    intervention = {
        "intervention_id": intervention_id,
        "job_id": request.job_id,
        "type": request.type,
        "message": request.message,
        "context": request.context,
        "options": request.options,
        "status": InterventionStatus.PENDING,
        "created_at": datetime.utcnow(),
        "responded_at": None,
        "response": None,
    }
    
    _interventions[intervention_id] = intervention
    logger.info(f"Created intervention {intervention_id} for job {request.job_id}")
    
    return InterventionRequest(**{
        k: v for k, v in intervention.items() if k != "response"
    })


@router.get("/{intervention_id}", response_model=InterventionRequest)
async def get_intervention(intervention_id: str):
    """Get intervention details."""
    if intervention_id not in _interventions:
        raise HTTPException(status_code=404, detail="Intervention not found")
    
    intervention = _interventions[intervention_id]
    return InterventionRequest(**{
        k: v for k, v in intervention.items() if k != "response"
    })


@router.post("/{intervention_id}/respond")
async def respond_to_intervention(intervention_id: str, response: InterventionResponse):
    """Submit human response to intervention."""
    if intervention_id not in _interventions:
        raise HTTPException(status_code=404, detail="Intervention not found")
    
    intervention = _interventions[intervention_id]
    
    if intervention["status"] != InterventionStatus.PENDING:
        raise HTTPException(status_code=400, detail="Intervention already responded to")
    
    # Update status based on decision
    if response.decision == "approved":
        intervention["status"] = InterventionStatus.APPROVED
    elif response.decision == "rejected":
        intervention["status"] = InterventionStatus.REJECTED
    else:
        intervention["status"] = InterventionStatus.MODIFIED
    
    intervention["responded_at"] = datetime.utcnow()
    intervention["response"] = response.model_dump()
    
    logger.info(f"Intervention {intervention_id} responded: {response.decision}")
    
    return {
        "message": "Response recorded",
        "intervention_id": intervention_id,
        "status": intervention["status"],
    }


@router.get("/")
async def list_interventions(
    job_id: str | None = None,
    status: InterventionStatus | None = None,
    limit: int = 50,
):
    """List interventions with filtering."""
    results = []
    
    for intervention in _interventions.values():
        if job_id and intervention["job_id"] != job_id:
            continue
        if status and intervention["status"] != status:
            continue
        
        results.append(InterventionRequest(**{
            k: v for k, v in intervention.items() if k != "response"
        }))
        
        if len(results) >= limit:
            break
    
    # Sort by created_at descending
    results.sort(key=lambda x: x.created_at, reverse=True)
    
    return {"interventions": results, "total": len(results)}


@router.get("/pending")
async def list_pending_interventions():
    """List all pending interventions requiring human action."""
    pending = [
        InterventionRequest(**{k: v for k, v in i.items() if k != "response"})
        for i in _interventions.values()
        if i["status"] == InterventionStatus.PENDING
    ]
    
    pending.sort(key=lambda x: x.created_at)
    
    return {"pending": pending, "count": len(pending)}
