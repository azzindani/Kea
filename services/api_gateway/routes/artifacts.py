"""
Artifacts API Routes.

Endpoints for artifact storage and retrieval.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from shared.logging import get_logger


logger = get_logger(__name__)

router = APIRouter()


# ============================================================================
# Models
# ============================================================================

class ArtifactMetadata(BaseModel):
    """Artifact metadata response."""
    artifact_id: str
    name: str
    content_type: str
    size_bytes: int
    job_id: str | None = None
    session_id: str | None = None
    tags: list[str] = []


class CreateArtifactRequest(BaseModel):
    """Create artifact request."""
    name: str
    content_type: str = "application/octet-stream"
    job_id: str | None = None
    session_id: str | None = None
    tags: list[str] = []


# In-memory store (use S3/Local in production)
_artifacts: dict[str, dict] = {}


# ============================================================================
# Routes
# ============================================================================

@router.post("/", response_model=ArtifactMetadata)
async def create_artifact(metadata: CreateArtifactRequest):
    """Create artifact metadata (content uploaded separately)."""
    import uuid
    
    artifact_id = f"art-{uuid.uuid4().hex[:12]}"
    
    artifact = {
        "artifact_id": artifact_id,
        "name": metadata.name,
        "content_type": metadata.content_type,
        "size_bytes": 0,
        "job_id": metadata.job_id,
        "session_id": metadata.session_id,
        "tags": metadata.tags,
        "content": None,
    }
    
    _artifacts[artifact_id] = artifact
    logger.info(f"Created artifact {artifact_id}")
    
    return ArtifactMetadata(**{k: v for k, v in artifact.items() if k != "content"})


@router.post("/{artifact_id}/upload")
async def upload_artifact_content(artifact_id: str, file: UploadFile = File(...)):
    """Upload artifact content."""
    if artifact_id not in _artifacts:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    content = await file.read()
    
    _artifacts[artifact_id]["content"] = content
    _artifacts[artifact_id]["size_bytes"] = len(content)
    _artifacts[artifact_id]["content_type"] = file.content_type or "application/octet-stream"
    
    logger.info(f"Uploaded content for {artifact_id}: {len(content)} bytes")
    
    return {"message": "Content uploaded", "size_bytes": len(content)}


@router.get("/{artifact_id}", response_model=ArtifactMetadata)
async def get_artifact_metadata(artifact_id: str):
    """Get artifact metadata."""
    if artifact_id not in _artifacts:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    artifact = _artifacts[artifact_id]
    return ArtifactMetadata(**{k: v for k, v in artifact.items() if k != "content"})


@router.get("/{artifact_id}/download")
async def download_artifact(artifact_id: str):
    """Download artifact content."""
    from fastapi.responses import Response
    
    if artifact_id not in _artifacts:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    artifact = _artifacts[artifact_id]
    
    if artifact["content"] is None:
        raise HTTPException(status_code=404, detail="No content uploaded")
    
    return Response(
        content=artifact["content"],
        media_type=artifact["content_type"],
        headers={"Content-Disposition": f'attachment; filename="{artifact["name"]}"'}
    )


@router.delete("/{artifact_id}")
async def delete_artifact(artifact_id: str):
    """Delete an artifact."""
    if artifact_id not in _artifacts:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    del _artifacts[artifact_id]
    logger.info(f"Deleted artifact {artifact_id}")
    
    return {"message": "Artifact deleted"}


@router.get("/")
async def list_artifacts(
    job_id: str | None = None,
    session_id: str | None = None,
    tag: str | None = None,
    limit: int = 50,
):
    """List artifacts with filtering."""
    results = []
    
    for artifact in _artifacts.values():
        if job_id and artifact["job_id"] != job_id:
            continue
        if session_id and artifact["session_id"] != session_id:
            continue
        if tag and tag not in artifact["tags"]:
            continue
        
        results.append(ArtifactMetadata(**{k: v for k, v in artifact.items() if k != "content"}))
        
        if len(results) >= limit:
            break
    
    return {"artifacts": results, "total": len(results)}
