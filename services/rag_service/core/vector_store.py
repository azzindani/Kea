"""
Vector Store Abstraction.

Provides a unified interface for Qdrant/Chroma vector storage.
"""

from __future__ import annotations

import os
import uuid
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from shared.logging import get_logger


logger = get_logger(__name__)


# ============================================================================
# Models
# ============================================================================

class Document(BaseModel):
    """Document to be stored in vector store."""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] | None = None


class SearchResult(BaseModel):
    """Search result from vector store."""
    id: str
    content: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Base Class
# ============================================================================

class VectorStore(ABC):
    """Abstract base class for vector stores."""
    
    @abstractmethod
    async def add(self, documents: list[Document]) -> list[str]:
        """Add documents to the store. Returns list of IDs."""
        pass
    
    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 10,
        filter: dict | None = None,
    ) -> list[SearchResult]:
        """Search for similar documents."""
        pass
    
    @abstractmethod
    async def get(self, ids: list[str]) -> list[Document]:
        """Get documents by ID."""
        pass
    
    @abstractmethod
    async def delete(self, ids: list[str]) -> None:
        """Delete documents by ID."""
        pass


# ============================================================================
# Qdrant Implementation
# ============================================================================

class QdrantVectorStore(VectorStore):
    """
    Qdrant vector store implementation.
    
    Uses Qwen3-Embedding-8B via OpenRouter for embeddings.
    Requires QDRANT_URL and optionally QDRANT_API_KEY.
    """
    
    def __init__(
        self,
        collection_name: str = "research_facts",
        embedding_dim: int = 1024,  # Qwen3 default
        use_local_embedding: bool = False,
    ) -> None:
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        self.use_local_embedding = use_local_embedding
        self._client = None
        self._embedding_provider = None
    
    async def _get_client(self):
        """Get or create Qdrant client."""
        if self._client is None:
            from qdrant_client import QdrantClient
            from qdrant_client.http.models import Distance, VectorParams
            
            url = os.getenv("QDRANT_URL", "http://localhost:6333")
            api_key = os.getenv("QDRANT_API_KEY")
            
            self._client = QdrantClient(url=url, api_key=api_key)
            
            # Ensure collection exists
            collections = self._client.get_collections()
            if self.collection_name not in [c.name for c in collections.collections]:
                self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE,
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
        
        return self._client
    
    async def _get_embedding(self, text: str) -> list[float]:
        """Get embedding for text using Qwen3 embedding provider."""
        if self._embedding_provider is None:
            from shared.embedding import create_embedding_provider
            
            self._embedding_provider = create_embedding_provider(
                use_local=self.use_local_embedding,
                dimension=self.embedding_dim,
            )
        
        return await self._embedding_provider.embed_query(text)
    
    async def add(self, documents: list[Document]) -> list[str]:
        """Add documents to Qdrant."""
        from qdrant_client.http.models import PointStruct
        
        client = await self._get_client()
        
        points = []
        for doc in documents:
            # Generate embedding if not provided
            if doc.embedding is None:
                doc.embedding = await self._get_embedding(doc.content)
            
            points.append(PointStruct(
                id=doc.id,
                vector=doc.embedding,
                payload={
                    "content": doc.content,
                    **doc.metadata,
                }
            ))
        
        client.upsert(collection_name=self.collection_name, points=points)
        
        logger.info(f"Added {len(documents)} documents to Qdrant")
        return [doc.id for doc in documents]
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        filter: dict | None = None,
    ) -> list[SearchResult]:
        """Search for similar documents."""
        client = await self._get_client()
        
        query_embedding = await self._get_embedding(query)
        
        # Use query_points for newer qdrant-client versions, fallback to search
        try:
            # Try newer API first (qdrant-client >= 1.10)
            from qdrant_client.http.models import QueryRequest
            results = client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=limit,
                query_filter=filter,
            ).points
        except (AttributeError, ImportError):
            # Fallback to older search API
            results = client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                query_filter=filter,
            )
        
        return [
            SearchResult(
                id=str(r.id),
                content=r.payload.get("content", "") if r.payload else "",
                score=r.score if hasattr(r, 'score') else 0.0,
                metadata={k: v for k, v in (r.payload or {}).items() if k != "content"},
            )
            for r in results
        ]
    
    async def get(self, ids: list[str]) -> list[Document]:
        """Get documents by ID."""
        client = await self._get_client()
        
        results = client.retrieve(
            collection_name=self.collection_name,
            ids=ids,
        )
        
        return [
            Document(
                id=str(r.id),
                content=r.payload.get("content", ""),
                metadata={k: v for k, v in r.payload.items() if k != "content"},
            )
            for r in results
        ]
    
    async def delete(self, ids: list[str]) -> None:
        """Delete documents by ID."""
        client = await self._get_client()
        
        client.delete(
            collection_name=self.collection_name,
            points_selector=ids,
        )
        
        logger.info(f"Deleted {len(ids)} documents from Qdrant")


# ============================================================================
# In-Memory Implementation (for testing)
# ============================================================================

class InMemoryVectorStore(VectorStore):
    """
    In-memory vector store for development/testing.
    
    Uses simple cosine similarity without actual embeddings.
    """
    
    def __init__(self) -> None:
        self._documents: dict[str, Document] = {}
    
    async def add(self, documents: list[Document]) -> list[str]:
        """Add documents to memory."""
        for doc in documents:
            self._documents[doc.id] = doc
        return [doc.id for doc in documents]
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        filter: dict | None = None,
    ) -> list[SearchResult]:
        """Search using simple text matching."""
        query_lower = query.lower()
        
        results = []
        for doc in self._documents.values():
            # Simple relevance score based on word overlap
            doc_words = set(doc.content.lower().split())
            query_words = set(query_lower.split())
            overlap = len(doc_words & query_words)
            
            if overlap > 0:
                score = overlap / max(len(query_words), 1)
                results.append(SearchResult(
                    id=doc.id,
                    content=doc.content,
                    score=score,
                    metadata=doc.metadata,
                ))
        
        # Sort by score and limit
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    async def get(self, ids: list[str]) -> list[Document]:
        """Get documents by ID."""
        return [self._documents[id] for id in ids if id in self._documents]
    
    async def delete(self, ids: list[str]) -> None:
        """Delete documents by ID."""
        for id in ids:
            self._documents.pop(id, None)


# ============================================================================
# Factory
# ============================================================================

def create_vector_store(use_memory: bool = False) -> VectorStore:
    """
    Create vector store based on configuration.
    
    Args:
        use_memory: Use in-memory store instead of Qdrant
        
    Returns:
        VectorStore instance (Qdrant if available, else InMemory)
    """
    if use_memory:
        logger.info("Using in-memory vector store (requested)")
        return InMemoryVectorStore()
    
    qdrant_url = os.getenv("QDRANT_URL")
    if not qdrant_url:
        logger.info("Using in-memory vector store (no QDRANT_URL)")
        return InMemoryVectorStore()
    
    # Try to connect to Qdrant, fallback to in-memory if unavailable
    try:
        from qdrant_client import QdrantClient
        
        api_key = os.getenv("QDRANT_API_KEY")
        client = QdrantClient(url=qdrant_url, api_key=api_key, timeout=5)
        
        # Test connection
        client.get_collections()
        
        logger.info(f"Using Qdrant vector store at {qdrant_url}")
        return QdrantVectorStore()
        
    except ImportError:
        logger.warning("qdrant_client not installed, using in-memory vector store")
        return InMemoryVectorStore()
        
    except Exception as e:
        logger.warning(f"Qdrant unavailable ({e}), using in-memory vector store")
        return InMemoryVectorStore()

