"""
Jobs API Routes.

Endpoints for research job management.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from shared.schemas import JobRequest, JobResponse, JobType, ResearchStatus
from shared.logging import get_logger


logger = get_logger(__name__)

router = APIRouter()

# In-memory job store (use Redis/PostgreSQL in production)
_jobs: dict[str, dict] = {}


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateJobRequest(BaseModel):
    """Create job request."""
    query: str = Field(..., min_length=1)
    job_type: JobType = JobType.DEEP_RESEARCH
    depth: int = Field(default=2, ge=1, le=5)
    max_sources: int = Field(default=10, ge=1, le=50)


class JobStatus(BaseModel):
    """Job status response."""
    job_id: str
    status: ResearchStatus
    progress: float
    created_at: datetime
    updated_at: datetime | None
    error: str | None = None


class JobResult(BaseModel):
    """Job result response."""
    job_id: str
    status: ResearchStatus
    report: str | None
    confidence: float
    facts_count: int
    sources_count: int
    artifact_ids: list[str]


# ============================================================================
# Routes
# ============================================================================

@router.post("/", response_model=JobStatus)
async def create_job(request: CreateJobRequest, background_tasks: BackgroundTasks):
    """
    Create a new research job.
    
    Returns job_id for tracking. Job runs in background.
    """
    job_id = f"job-{uuid.uuid4().hex[:12]}"
    
    job = {
        "job_id": job_id,
        "query": request.query,
        "job_type": request.job_type,
        "depth": request.depth,
        "max_sources": request.max_sources,
        "status": ResearchStatus.PENDING,
        "progress": 0.0,
        "created_at": datetime.utcnow(),
        "updated_at": None,
        "error": None,
        "result": None,
    }
    
    _jobs[job_id] = job
    
    logger.info(f"Created job {job_id}", extra={"query": request.query[:100]})
    
    # Queue background task
    # background_tasks.add_task(run_research_job, job_id)
    
    return JobStatus(
        job_id=job_id,
        status=ResearchStatus.PENDING,
        progress=0.0,
        created_at=job["created_at"],
        updated_at=None,
    )


@router.get("/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get job status."""
    job = _jobs.get(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatus(
        job_id=job["job_id"],
        status=job["status"],
        progress=job["progress"],
        created_at=job["created_at"],
        updated_at=job.get("updated_at"),
        error=job.get("error"),
    )


@router.get("/{job_id}/result", response_model=JobResult)
async def get_job_result(job_id: str):
    """Get job result (only available for completed jobs)."""
    job = _jobs.get(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != ResearchStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Current status: {job['status']}"
        )
    
    result = job.get("result", {})
    
    return JobResult(
        job_id=job_id,
        status=job["status"],
        report=result.get("report"),
        confidence=result.get("confidence", 0.0),
        facts_count=result.get("facts_count", 0),
        sources_count=result.get("sources_count", 0),
        artifact_ids=result.get("artifact_ids", []),
    )


@router.delete("/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a pending or running job."""
    job = _jobs.get(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] in [ResearchStatus.COMPLETED, ResearchStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed/failed job")
    
    job["status"] = ResearchStatus.CANCELLED
    job["updated_at"] = datetime.utcnow()
    
    logger.info(f"Cancelled job {job_id}")
    
    return {"message": "Job cancelled", "job_id": job_id}


@router.get("/")
async def list_jobs(
    status: ResearchStatus | None = None,
    limit: int = 20,
    offset: int = 0,
):
    """List jobs with optional filtering."""
    jobs = list(_jobs.values())
    
    if status:
        jobs = [j for j in jobs if j["status"] == status]
    
    # Sort by created_at descending
    jobs.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "jobs": jobs[offset:offset + limit],
        "total": len(jobs),
        "limit": limit,
        "offset": offset,
    }
