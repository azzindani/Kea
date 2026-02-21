"""
Jobs API Routes.

- Uses PostgreSQL for persistent job storage
- Implements background task execution via Orchestrator API
- Requires authentication for job operations
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from shared.schemas import JobType, JobStatus
from shared.logging.main import get_logger
from shared.database.connection import get_database_pool
from shared.users.models import User
from services.api_gateway.middleware.auth import get_current_user_required
from shared.config import get_settings


logger = get_logger(__name__)

router = APIRouter()

# Orchestrator URL for API calls
from shared.service_registry import ServiceRegistry, ServiceName
ORCHESTRATOR_URL = ServiceRegistry.get_url(ServiceName.ORCHESTRATOR)


# ============================================================================
# Database Setup
# ============================================================================

CREATE_JOBS_TABLE = """
CREATE TABLE IF NOT EXISTS system_jobs (
    job_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    query TEXT NOT NULL,
    job_type TEXT NOT NULL,
    depth INTEGER DEFAULT 2,
    max_steps INTEGER DEFAULT 20,
    status TEXT NOT NULL,
    progress REAL DEFAULT 0.0,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ,
    error TEXT,
    output TEXT,
    confidence REAL DEFAULT 0.0,
    steps_count INTEGER DEFAULT 0,
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
    
    Uses PostgreSQL for job persistence.
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
        max_steps: int,
    ) -> dict:
        """Create new job in database."""
        await self.initialize()
        pool = await get_database_pool()
        
        now = datetime.utcnow()
        
        await pool.execute(
            """
            INSERT INTO system_jobs 
            (job_id, user_id, query, job_type, depth, max_steps, status, progress, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            job_id, user_id, query, job_type.value, depth, max_steps,
            JobStatus.PENDING.value, 0.0, now,
        )
        
        return {
            "job_id": job_id,
            "user_id": user_id,
            "query": query,
            "job_type": job_type,
            "depth": depth,
            "max_steps": max_steps,
            "status": JobStatus.PENDING,
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
            "SELECT * FROM system_jobs WHERE job_id = $1",
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
            if isinstance(value, JobStatus):
                value = value.value
            values.append(value)
        
        values.append(job_id)
        
        await pool.execute(
            f"UPDATE system_jobs SET {', '.join(set_parts)} WHERE job_id = ${param_index}",
            *values,
        )
    
    async def list_for_user(
        self,
        user_id: str,
        status: Optional[JobStatus] = None,
        limit: int = None,
        offset: int = 0,
    ) -> list[dict]:
        """List jobs for a user."""
        limit = limit or get_settings().jobs.default_limit
        await self.initialize()
        pool = await get_database_pool()
        
        if status:
            rows = await pool.fetch(
                """
                SELECT * FROM system_jobs 
                WHERE user_id = $1 AND status = $2
                ORDER BY created_at DESC
                LIMIT $3 OFFSET $4
                """,
                user_id, status.value, limit, offset,
            )
        else:
            rows = await pool.fetch(
                """
                SELECT * FROM system_jobs 
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                user_id, limit, offset,
            )
        
        return [self._row_to_dict(row) for row in rows]
    
    async def count_for_user(self, user_id: str, status: Optional[JobStatus] = None) -> int:
        """Count jobs for user."""
        await self.initialize()
        pool = await get_database_pool()
        
        if status:
            result = await pool.fetchrow(
                "SELECT COUNT(*) as cnt FROM system_jobs WHERE user_id = $1 AND status = $2",
                user_id, status.value,
            )
        else:
            result = await pool.fetchrow(
                "SELECT COUNT(*) as cnt FROM system_jobs WHERE user_id = $1",
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
            "max_steps": row["max_steps"],
            "status": JobStatus(row["status"]),
            "progress": row["progress"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "error": row["error"],
            "output": row["output"],
            "confidence": row["confidence"] if row["confidence"] is not None else 0.0,
            "steps_count": row["steps_count"] if row["steps_count"] is not None else 0,
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
# Background Task: Run System Job
# ============================================================================

async def run_system_job(
    job_id: str,
):
    """
    Execute job via Orchestrator API.
    """
    store = await get_job_store()
    job = await store.get(job_id)
    
    if not job:
        logger.error(f"Job {job_id} not found for execution")
        return
    
    # Update status to running
    await store.update(job_id, status=JobStatus.RUNNING, progress=0.1)
    
    logger.info(f"Starting system job {job_id}", 
                extra={"query": job["query"][:100]})
    
    try:
        from services.api_gateway.clients.orchestrator import get_orchestrator_client
        client = await get_orchestrator_client()
        
        # Start execution via client
        result = await client.start_execution(
            query=job["query"],
            depth=job["depth"],
            max_steps=job["max_steps"],
        )
        
        # Update job with results
        await store.update(
            job_id,
            status=JobStatus.COMPLETED,
            progress=1.0,
            output=result.get("output", ""),
            confidence=result.get("confidence", 0.0),
            steps_count=result.get("steps_count", 0),
        )
        
        logger.info(f"System job {job_id} completed", extra={
            "confidence": result.get("confidence", 0.0),
            "steps_count": result.get("steps_count", 0),
        })
        
    except Exception as e:
        logger.error(f"System job {job_id} failed: {e}")
        await store.update(
            job_id,
            status=JobStatus.FAILED,
            error=str(e),
        )


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateJobRequest(BaseModel):
    """Create job request."""
    query: str = Field(..., min_length=1)
    job_type: JobType = JobType.AUTONOMOUS
    depth: int = Field(
        default_factory=lambda: get_settings().kernel.default_depth, 
        ge=1, 
        le=get_settings().kernel.max_depth
    )
    max_steps: int = Field(
        default_factory=lambda: get_settings().kernel.default_max_steps, 
        ge=1, 
        le=get_settings().kernel.max_steps
    )


class JobStatusResponse(BaseModel):
    """Job status response."""
    job_id: str
    status: JobStatus
    progress: float
    created_at: datetime
    updated_at: datetime | None
    error: str | None = None


class JobResult(BaseModel):
    """Job result response."""
    job_id: str
    status: JobStatus
    output: str | None
    confidence: float
    steps_count: int
    artifact_ids: list[str]


# ============================================================================
# Routes
# ============================================================================

@router.post("/", response_model=JobStatusResponse)
async def create_job(
    request: CreateJobRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user_required),
):
    """
    Create a new system job.
    
    Returns job_id for tracking. Job runs in background.
    Requires authentication.
    """
    job_id = f"{get_settings().jobs.id_prefix}{uuid.uuid4().hex[:12]}"
    store = await get_job_store()
    
    job = await store.create(
        job_id=job_id,
        user_id=user.user_id,
        query=request.query,
        job_type=request.job_type,
        depth=request.depth,
        max_steps=request.max_steps,
    )
    
    logger.info(f"Created job {job_id}", extra={
        "query": request.query[:100],
        "user_id": user.user_id,
    })
    
    # Queue background task to execute job
    background_tasks.add_task(
        run_system_job, 
        job_id, 
    )
    
    return JobStatusResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        progress=0.0,
        created_at=job["created_at"],
        updated_at=None,
    )


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    user: User = Depends(get_current_user_required),
):
    """Get job status. Requires authentication."""
    store = await get_job_store()
    job = await store.get(job_id)
    
    if not job:
        raise HTTPException(
            status_code=get_settings().status_codes.not_found, 
            detail="Job not found"
        )
    
    # Check ownership
    if job["user_id"] != user.user_id:
        raise HTTPException(
            status_code=get_settings().status_codes.forbidden, 
            detail="Access denied"
        )
    
    return JobStatusResponse(
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
        raise HTTPException(
            status_code=get_settings().status_codes.not_found, 
            detail="Job not found"
        )
    
    if job["user_id"] != user.user_id:
        raise HTTPException(
            status_code=get_settings().status_codes.forbidden, 
            detail="Access denied"
        )
    
    if job["status"] != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=get_settings().status_codes.bad_request,
            detail=f"Job not completed. Current status: {job['status'].value}"
        )
    
    return JobResult(
        job_id=job_id,
        status=job["status"],
        output=job.get("output"),
        confidence=job.get("confidence", 0.0),
        steps_count=job.get("steps_count", 0),
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
        raise HTTPException(
            status_code=get_settings().status_codes.not_found, 
            detail="Job not found"
        )
    
    if job["user_id"] != user.user_id:
        raise HTTPException(
            status_code=get_settings().status_codes.forbidden, 
            detail="Access denied"
        )
    
    if job["status"] in [JobStatus.COMPLETED, JobStatus.FAILED]:
        raise HTTPException(
            status_code=get_settings().status_codes.bad_request, 
            detail="Cannot cancel completed/failed job"
        )
    
    await store.update(job_id, status=JobStatus.CANCELLED)
    
    logger.info(f"Cancelled job {job_id}", extra={"user_id": user.user_id})
    
    return {"message": "Job cancelled", "job_id": job_id}


@router.get("/")
async def list_jobs(
    status: JobStatus | None = None,
    limit: int = Query(get_settings().jobs.default_limit, ge=1, le=get_settings().jobs.max_limit),
    offset: int = Query(0, ge=0),
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
            JobStatusResponse(
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
