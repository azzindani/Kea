"""
Jobs API Routes.

Endpoints for research job management with persistent storage.

Changes:
- Uses database for persistent job storage (PostgreSQL/SQLite)
- Implements background task execution via Orchestrator API
- Requires authentication for job operations
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any, Optional

import httpx
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from shared.schemas import JobRequest, JobResponse, JobType, ResearchStatus
from shared.logging import get_logger
from shared.database.connection import get_database_pool
from shared.users import User
from services.api_gateway.middleware.auth import get_current_user, get_current_user_required


logger = get_logger(__name__)

router = APIRouter()

# Orchestrator URL for API calls
import os
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")


# ============================================================================
# Database Setup
# ============================================================================

CREATE_JOBS_TABLE = """
CREATE TABLE IF NOT EXISTS research_jobs (
    job_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    query TEXT NOT NULL,
    job_type TEXT NOT NULL,
    depth INTEGER DEFAULT 2,
    max_sources INTEGER DEFAULT 10,
    status TEXT NOT NULL,
    progress REAL DEFAULT 0.0,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    error TEXT,
    report TEXT,
    confidence REAL DEFAULT 0.0,
    facts_count INTEGER DEFAULT 0,
    sources_count INTEGER DEFAULT 0,
    artifact_ids TEXT
)
"""


async def ensure_table_exists():
    """Create jobs table if not exists."""
    try:
        pool = await get_database_pool()
        await pool.execute(CREATE_JOBS_TABLE)
        logger.debug("Jobs table ensured")
    except Exception as e:
        logger.warning(f"Could not create jobs table (may already exist): {e}")


# ============================================================================
# Job Storage Class
# ============================================================================

class JobStore:
    """
    Database-backed job storage.
    
    Supports both PostgreSQL and SQLite.
    """
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self):
        """Initialize job store."""
        if self._initialized:
            return
        await ensure_table_exists()
        self._initialized = True
    
    async def create(
        self,
        job_id: str,
        user_id: str,
        query: str,
        job_type: JobType,
        depth: int,
        max_sources: int,
    ) -> dict:
        """Create new job in database."""
        await self.initialize()
        pool = await get_database_pool()
        
        now = datetime.utcnow()
        
        await pool.execute(
            """
            INSERT INTO research_jobs 
            (job_id, user_id, query, job_type, depth, max_sources, status, progress, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            job_id, user_id, query, job_type.value, depth, max_sources,
            ResearchStatus.PENDING.value, 0.0, now,
        )
        
        return {
            "job_id": job_id,
            "user_id": user_id,
            "query": query,
            "job_type": job_type,
            "depth": depth,
            "max_sources": max_sources,
            "status": ResearchStatus.PENDING,
            "progress": 0.0,
            "created_at": now,
            "updated_at": None,
            "error": None,
        }
    
    async def get(self, job_id: str) -> Optional[dict]:
        """Get job by ID."""
        await self.initialize()
        pool = await get_database_pool()
        
        row = await pool.fetchrow(
            "SELECT * FROM research_jobs WHERE job_id = $1",
            job_id,
        )
        
        if not row:
            return None
        
        return self._row_to_dict(row)
    
    async def update(self, job_id: str, **kwargs) -> None:
        """Update job fields."""
        await self.initialize()
        pool = await get_database_pool()
        
        kwargs["updated_at"] = datetime.utcnow()
        
        # Build SET clause with PostgreSQL placeholders ($1, $2, etc.)
        set_parts = []
        values = []
        param_index = 1
        for key, value in kwargs.items():
            set_parts.append(f"{key} = ${param_index}")
            param_index += 1
            if isinstance(value, ResearchStatus):
                value = value.value
            values.append(value)
        
        values.append(job_id)
        
        await pool.execute(
            f"UPDATE research_jobs SET {', '.join(set_parts)} WHERE job_id = ${param_index}",
            *values,
        )
    
    async def list_for_user(
        self,
        user_id: str,
        status: Optional[ResearchStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """List jobs for a user."""
        await self.initialize()
        pool = await get_database_pool()
        
        if status:
            rows = await pool.fetch(
                """
                SELECT * FROM research_jobs 
                WHERE user_id = $1 AND status = $2
                ORDER BY created_at DESC
                LIMIT $3 OFFSET $4
                """,
                user_id, status.value, limit, offset,
            )
        else:
            rows = await pool.fetch(
                """
                SELECT * FROM research_jobs 
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                user_id, limit, offset,
            )
        
        return [self._row_to_dict(row) for row in rows]
    
    async def count_for_user(self, user_id: str, status: Optional[ResearchStatus] = None) -> int:
        """Count jobs for user."""
        await self.initialize()
        pool = await get_database_pool()
        
        if status:
            result = await pool.fetchrow(
                "SELECT COUNT(*) as cnt FROM research_jobs WHERE user_id = $1 AND status = $2",
                user_id, status.value,
            )
        else:
            result = await pool.fetchrow(
                "SELECT COUNT(*) as cnt FROM research_jobs WHERE user_id = $1",
                user_id,
            )
        
        return result["cnt"] if result else 0
    
    def _row_to_dict(self, row) -> dict:
        """Convert database row to dict."""
        return {
            "job_id": row["job_id"],
            "user_id": row["user_id"],
            "query": row["query"],
            "job_type": JobType(row["job_type"]),
            "depth": row["depth"],
            "max_sources": row["max_sources"],
            "status": ResearchStatus(row["status"]),
            "progress": row["progress"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "error": row["error"],
            "report": row["report"],
            "confidence": row["confidence"] if row["confidence"] is not None else 0.0,
            "facts_count": row["facts_count"] if row["facts_count"] is not None else 0,
            "sources_count": row["sources_count"] if row["sources_count"] is not None else 0,
            "artifact_ids": row["artifact_ids"].split(",") if row["artifact_ids"] else [],
        }


# Singleton job store
_job_store: Optional[JobStore] = None


async def get_job_store() -> JobStore:
    """Get singleton job store."""
    global _job_store
    if _job_store is None:
        _job_store = JobStore()
    return _job_store


# ============================================================================
# Background Task: Run Research Job
# ============================================================================

async def run_research_job(job_id: str):
    """
    Execute research job via Orchestrator API.
    
    This is the background task that actually runs the research.
    """
    store = await get_job_store()
    job = await store.get(job_id)
    
    if not job:
        logger.error(f"Job {job_id} not found for execution")
        return
    
    # Update status to running
    await store.update(job_id, status=ResearchStatus.RUNNING, progress=0.1)
    
    logger.info(f"Starting research job {job_id}", extra={"query": job["query"][:100]})
    
    try:
        # Call Orchestrator's research endpoint via API
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{ORCHESTRATOR_URL}/research",
                json={
                    "query": job["query"],
                    "depth": job["depth"],
                    "max_sources": job["max_sources"],
                },
            )
            
            if response.status_code != 200:
                raise Exception(f"Orchestrator returned {response.status_code}: {response.text}")
            
            result = response.json()
        
        # Update job with results
        await store.update(
            job_id,
            status=ResearchStatus.COMPLETED,
            progress=1.0,
            report=result.get("report", ""),
            confidence=result.get("confidence", 0.0),
            facts_count=result.get("facts_count", 0),
            sources_count=result.get("sources_count", 0),
        )
        
        logger.info(f"Research job {job_id} completed", extra={
            "confidence": result.get("confidence", 0.0),
            "sources_count": result.get("sources_count", 0),
        })
        
    except Exception as e:
        logger.error(f"Research job {job_id} failed: {e}")
        await store.update(
            job_id,
            status=ResearchStatus.FAILED,
            error=str(e),
        )


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
async def create_job(
    request: CreateJobRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user_required),
):
    """
    Create a new research job.
    
    Returns job_id for tracking. Job runs in background.
    Requires authentication.
    """
    job_id = f"job-{uuid.uuid4().hex[:12]}"
    store = await get_job_store()
    
    job = await store.create(
        job_id=job_id,
        user_id=user.user_id,
        query=request.query,
        job_type=request.job_type,
        depth=request.depth,
        max_sources=request.max_sources,
    )
    
    logger.info(f"Created job {job_id}", extra={
        "query": request.query[:100],
        "user_id": user.user_id,
    })
    
    # Queue background task to execute job
    background_tasks.add_task(run_research_job, job_id)
    
    return JobStatus(
        job_id=job_id,
        status=ResearchStatus.PENDING,
        progress=0.0,
        created_at=job["created_at"],
        updated_at=None,
    )


@router.get("/{job_id}", response_model=JobStatus)
async def get_job_status(
    job_id: str,
    user: User = Depends(get_current_user_required),
):
    """Get job status. Requires authentication."""
    store = await get_job_store()
    job = await store.get(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check ownership
    if job["user_id"] != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return JobStatus(
        job_id=job["job_id"],
        status=job["status"],
        progress=job["progress"],
        created_at=job["created_at"],
        updated_at=job.get("updated_at"),
        error=job.get("error"),
    )


@router.get("/{job_id}/result", response_model=JobResult)
async def get_job_result(
    job_id: str,
    user: User = Depends(get_current_user_required),
):
    """Get job result (only available for completed jobs). Requires authentication."""
    store = await get_job_store()
    job = await store.get(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["user_id"] != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if job["status"] != ResearchStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Current status: {job['status'].value}"
        )
    
    return JobResult(
        job_id=job_id,
        status=job["status"],
        report=job.get("report"),
        confidence=job.get("confidence", 0.0),
        facts_count=job.get("facts_count", 0),
        sources_count=job.get("sources_count", 0),
        artifact_ids=job.get("artifact_ids", []),
    )


@router.delete("/{job_id}")
async def cancel_job(
    job_id: str,
    user: User = Depends(get_current_user_required),
):
    """Cancel a pending or running job. Requires authentication."""
    store = await get_job_store()
    job = await store.get(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["user_id"] != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if job["status"] in [ResearchStatus.COMPLETED, ResearchStatus.FAILED]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed/failed job")
    
    await store.update(job_id, status=ResearchStatus.CANCELLED)
    
    logger.info(f"Cancelled job {job_id}", extra={"user_id": user.user_id})
    
    return {"message": "Job cancelled", "job_id": job_id}


@router.get("/")
async def list_jobs(
    status: ResearchStatus | None = None,
    limit: int = 20,
    offset: int = 0,
    user: User = Depends(get_current_user_required),
):
    """List jobs for current user. Requires authentication."""
    store = await get_job_store()
    
    jobs = await store.list_for_user(
        user_id=user.user_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    total = await store.count_for_user(user.user_id, status)
    
    return {
        "jobs": [
            JobStatus(
                job_id=j["job_id"],
                status=j["status"],
                progress=j["progress"],
                created_at=j["created_at"],
                updated_at=j.get("updated_at"),
                error=j.get("error"),
            )
            for j in jobs
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
