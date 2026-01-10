# RAG Service Core Package
"""
Core components for the RAG service.

- vector_store: Vector storage abstraction (Qdrant/In-Memory)
- fact_store: Atomic fact storage and search
- artifact_store: Research artifact storage (Local/S3)
"""

from services.rag_service.core.vector_store import (
    VectorStore,
    QdrantVectorStore,
    InMemoryVectorStore,
    Document,
    SearchResult,
    create_vector_store,
)
from services.rag_service.core.fact_store import FactStore
from services.rag_service.core.artifact_store import (
    ArtifactStore,
    LocalArtifactStore,
    S3ArtifactStore,
    Artifact,
    create_artifact_store,
)

__all__ = [
    "VectorStore",
    "QdrantVectorStore",
    "InMemoryVectorStore",
    "Document",
    "SearchResult",
    "create_vector_store",
    "FactStore",
    "ArtifactStore",
    "LocalArtifactStore",
    "S3ArtifactStore",
    "Artifact",
    "create_artifact_store",
]
