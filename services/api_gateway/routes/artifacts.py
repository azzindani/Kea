"""
Artifacts API Routes.

Endpoints for artifact storage and retrieval.
Refactored for v0.4.0 to use RAG Service for persistent artifact storage.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Response
from pydantic import BaseModel, Field

from shared.logging.main import get_logger
from services.api_gateway.clients.rag_service import RAGServiceClient


logger = get_logger(__name__)

router = APIRouter()


# ============================================================================
# Models
# ============================================================================

class ArtifactMetadata(BaseModel):
    """Artifact metadata response."""
    artifact_id: str
    name: str
    content_type: str = "application/octet-stream"
    size_bytes: int = 0
    job_id: str | None = None
    tags: list[str] = []


# ============================================================================
# Dependency
# ============================================================================

async def get_rag_client() -> RAGServiceClient:
    """Get RAG service client instance."""
    return RAGServiceClient()


# ============================================================================
# Routes
# ============================================================================

@router.post("/", response_model=ArtifactMetadata)
async def create_artifact(
    file: UploadFile = File(...),
    job_id: str | None = None,
    client: RAGServiceClient = Depends(get_rag_client)
):
    """
    Upload and store an artifact.
    
    In v0.4.0, all artifacts are persisted via the RAG Service.
    """
    try:
        content = await file.read()
        artifact_id = await client.store_artifact(
            name=file.filename or "unnamed_artifact",
            content=content,
            content_type=file.content_type or "application/octet-stream"
        )
        
        logger.info(f"Stored artifact {artifact_id} via RAG Service")
        
        return ArtifactMetadata(
            artifact_id=artifact_id,
            name=file.filename or "unnamed_artifact",
            content_type=file.content_type or "application/octet-stream",
            size_bytes=len(content),
            job_id=job_id
        )
    except Exception as e:
        logger.error(f"Failed to store artifact: {e}")
        raise HTTPException(status_code=500, detail=f"RAG Service error: {str(e)}")


@router.get("/{artifact_id}/download")
async def download_artifact(
    artifact_id: str,
    client: RAGServiceClient = Depends(get_rag_client)
):
    """Download artifact content from the RAG Service."""
    try:
        content = await client.get_artifact(artifact_id)
        
        if content is None:
            raise HTTPException(status_code=404, detail="Artifact not found")
        
        return Response(
            content=content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="artifact_{artifact_id}"'}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download artifact {artifact_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_artifacts():
    """
    List artifacts.
    Note: Currently RAG Service doesn't expose a listing API for raw artifacts.
    This would require a database query to the artifacts table.
    """
    return {"message": "Listing artifacts not yet supported in this mode", "artifacts": []}
