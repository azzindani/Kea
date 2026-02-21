"""
Artifact Store.

Storage for system artifacts (reports, data files, etc).
"""

from __future__ import annotations

import hashlib
import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from shared.logging import get_logger


logger = get_logger(__name__)


# ============================================================================
# Models
# ============================================================================

class Artifact(BaseModel):
    """Artifact metadata."""
    artifact_id: str = Field(default_factory=lambda: f"art-{uuid.uuid4().hex[:12]}")
    name: str
    content_type: str = "application/octet-stream"
    size_bytes: int = 0
    checksum: str = ""
    
    job_id: str | None = None
    session_id: str | None = None
    
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Base Class
# ============================================================================

class ArtifactStore(ABC):
    """Abstract base class for artifact storage."""
    
    @abstractmethod
    async def put(self, artifact: Artifact, content: bytes) -> str:
        """Store artifact content. Returns artifact ID."""
        pass
    
    @abstractmethod
    async def get(self, artifact_id: str) -> tuple[Artifact, bytes] | None:
        """Get artifact and its content."""
        pass
    
    @abstractmethod
    async def get_metadata(self, artifact_id: str) -> Artifact | None:
        """Get artifact metadata only."""
        pass
    
    @abstractmethod
    async def delete(self, artifact_id: str) -> None:
        """Delete artifact."""
        pass
    
    @abstractmethod
    async def list(
        self,
        job_id: str | None = None,
        session_id: str | None = None,
        limit: int = 100,
    ) -> list[Artifact]:
        """List artifacts with optional filtering."""
        pass


# ============================================================================
# Local File System Implementation
# ============================================================================

class LocalArtifactStore(ArtifactStore):
    """
    Local file system artifact store.
    
    Stores artifacts in a directory structure:
    {base_path}/
        {artifact_id}/
            metadata.json
            content
    """
    
    def __init__(self, base_path: str = "./artifacts") -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _artifact_dir(self, artifact_id: str) -> Path:
        return self.base_path / artifact_id
    
    async def put(self, artifact: Artifact, content: bytes) -> str:
        """Store artifact locally."""
        import json
        
        # Compute checksum
        artifact.checksum = hashlib.sha256(content).hexdigest()
        artifact.size_bytes = len(content)
        
        # Create directory
        artifact_dir = self._artifact_dir(artifact.artifact_id)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        
        # Write metadata
        metadata_path = artifact_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(artifact.model_dump(mode="json"), f, indent=2, default=str)
        
        # Write content
        content_path = artifact_dir / "content"
        with open(content_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Stored artifact {artifact.artifact_id}", extra={"size": len(content)})
        return artifact.artifact_id
    
    async def get(self, artifact_id: str) -> tuple[Artifact, bytes] | None:
        """Get artifact and content."""
        import json
        
        artifact_dir = self._artifact_dir(artifact_id)
        
        if not artifact_dir.exists():
            return None
        
        # Read metadata
        metadata_path = artifact_dir / "metadata.json"
        with open(metadata_path) as f:
            metadata = json.load(f)
        
        artifact = Artifact(**metadata)
        
        # Read content
        content_path = artifact_dir / "content"
        with open(content_path, "rb") as f:
            content = f.read()
        
        return artifact, content
    
    async def get_metadata(self, artifact_id: str) -> Artifact | None:
        """Get artifact metadata only."""
        import json
        
        metadata_path = self._artifact_dir(artifact_id) / "metadata.json"
        
        if not metadata_path.exists():
            return None
        
        with open(metadata_path) as f:
            metadata = json.load(f)
        
        return Artifact(**metadata)
    
    async def delete(self, artifact_id: str) -> None:
        """Delete artifact."""
        import shutil
        
        artifact_dir = self._artifact_dir(artifact_id)
        
        if artifact_dir.exists():
            shutil.rmtree(artifact_dir)
            logger.info(f"Deleted artifact {artifact_id}")
    
    async def list(
        self,
        job_id: str | None = None,
        session_id: str | None = None,
        limit: int = 100,
    ) -> list[Artifact]:
        """List artifacts."""
        import json
        
        artifacts = []
        
        for artifact_dir in self.base_path.iterdir():
            if not artifact_dir.is_dir():
                continue
            
            metadata_path = artifact_dir / "metadata.json"
            if not metadata_path.exists():
                continue
            
            with open(metadata_path) as f:
                metadata = json.load(f)
            
            artifact = Artifact(**metadata)
            
            # Apply filters
            if job_id and artifact.job_id != job_id:
                continue
            if session_id and artifact.session_id != session_id:
                continue
            
            artifacts.append(artifact)
            
            if len(artifacts) >= limit:
                break
        
        # Sort by created_at descending
        artifacts.sort(key=lambda x: x.created_at, reverse=True)
        return artifacts


# ============================================================================
# S3 Implementation
# ============================================================================

class S3ArtifactStore(ArtifactStore):
    """
    S3-compatible artifact store.
    
    Works with AWS S3, MinIO, and other compatible services.
    """
    
    def __init__(
        self,
        bucket: str | None = None,
        endpoint: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
    ) -> None:
        from shared.config import get_settings
        settings = get_settings()
        self.bucket = bucket or settings.s3.bucket
        self.endpoint = endpoint or settings.s3.endpoint
        self.access_key = access_key or settings.s3.access_key
        self.secret_key = secret_key or settings.s3.secret_key
        self._client = None
    
    def _get_client(self):
        """Get or create S3 client."""
        if self._client is None:
            import boto3
            
            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            )
        
        return self._client
    
    async def put(self, artifact: Artifact, content: bytes) -> str:
        """Store artifact in S3."""
        import json
        
        client = self._get_client()
        
        artifact.checksum = hashlib.sha256(content).hexdigest()
        artifact.size_bytes = len(content)
        
        # Store content
        client.put_object(
            Bucket=self.bucket,
            Key=f"{artifact.artifact_id}/content",
            Body=content,
            ContentType=artifact.content_type,
        )
        
        # Store metadata
        metadata_json = artifact.model_dump_json()
        client.put_object(
            Bucket=self.bucket,
            Key=f"{artifact.artifact_id}/metadata.json",
            Body=metadata_json.encode(),
            ContentType="application/json",
        )
        
        logger.info(f"Stored artifact {artifact.artifact_id} in S3")
        return artifact.artifact_id
    
    async def get(self, artifact_id: str) -> tuple[Artifact, bytes] | None:
        """Get artifact from S3."""
        import json
        
        client = self._get_client()
        
        try:
            # Get metadata
            response = client.get_object(
                Bucket=self.bucket,
                Key=f"{artifact_id}/metadata.json",
            )
            metadata = json.loads(response["Body"].read().decode())
            artifact = Artifact(**metadata)
            
            # Get content
            response = client.get_object(
                Bucket=self.bucket,
                Key=f"{artifact_id}/content",
            )
            content = response["Body"].read()
            
            return artifact, content
            
        except Exception:
            return None
    
    async def get_metadata(self, artifact_id: str) -> Artifact | None:
        """Get artifact metadata from S3."""
        import json
        
        client = self._get_client()
        
        try:
            response = client.get_object(
                Bucket=self.bucket,
                Key=f"{artifact_id}/metadata.json",
            )
            metadata = json.loads(response["Body"].read().decode())
            return Artifact(**metadata)
        except Exception:
            return None
    
    async def delete(self, artifact_id: str) -> None:
        """Delete artifact from S3."""
        client = self._get_client()
        
        client.delete_objects(
            Bucket=self.bucket,
            Delete={
                "Objects": [
                    {"Key": f"{artifact_id}/content"},
                    {"Key": f"{artifact_id}/metadata.json"},
                ]
            }
        )
        
        logger.info(f"Deleted artifact {artifact_id} from S3")
    
    async def list(
        self,
        job_id: str | None = None,
        session_id: str | None = None,
        limit: int = 100,
    ) -> list[Artifact]:
        """List artifacts from S3."""
        # Simplified implementation - would need pagination for large buckets
        client = self._get_client()
        
        response = client.list_objects_v2(
            Bucket=self.bucket,
            MaxKeys=limit * 2,
        )
        
        artifacts = []
        seen_ids = set()
        
        for obj in response.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/metadata.json"):
                artifact_id = key.rsplit("/", 1)[0]
                if artifact_id not in seen_ids:
                    seen_ids.add(artifact_id)
                    artifact = await self.get_metadata(artifact_id)
                    if artifact:
                        artifacts.append(artifact)
        
        return artifacts[:limit]


# ============================================================================
# Factory
# ============================================================================

def create_artifact_store(use_local: bool | None = None) -> ArtifactStore:
    """
    Create artifact store based on configuration.
    
    Args:
        use_local: Use local storage instead of S3
    """
    from shared.config import get_settings
    settings = get_settings()
    
    if use_local is None:
        # Default to local if S3 not configured or explicitly disabled
        use_local = not bool(settings.s3.bucket and settings.s3.access_key)
        
    # 1. Create Blob Layer (Physical Storage)
    if use_local:
        logger.info("Using local artifact blob store")
        blob_store = LocalArtifactStore()
    else:
        logger.info("Using S3 artifact blob store")
        blob_store = S3ArtifactStore()

    # 2. Add Metadata Layer (Postgres Index)
    if settings.database.url or os.getenv("DATABASE_URL"):
        try:
            from services.rag_service.core.postgres_artifacts import PostgresArtifactStore
            logger.info("Using Postgres artifact metadata index")
            return PostgresArtifactStore(blob_store)
        except Exception as e:
            logger.warning(f"Failed to init PostgresArtifactStore: {e}, using blob store only")
            
    return blob_store
