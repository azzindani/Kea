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
    
    Requires QDRANT_URL and optionally QDRANT_API_KEY.
    """
    
    def __init__(
        self,
        collection_name: str = "research_facts",
        embedding_dim: int = 1536,
    ) -> None:
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        self._client = None
    
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
        """Get embedding for text using OpenRouter."""
        import httpx
        
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/embeddings",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "openai/text-embedding-3-small",
                    "input": text,
                }
            )
            response.raise_for_status()
            data = response.json()
        
        return data["data"][0]["embedding"]
    
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
        
        results = client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit,
            query_filter=filter,
        )
        
        return [
            SearchResult(
                id=str(r.id),
                content=r.payload.get("content", ""),
                score=r.score,
                metadata={k: v for k, v in r.payload.items() if k != "content"},
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
    """
    if use_memory or not os.getenv("QDRANT_URL"):
        logger.info("Using in-memory vector store")
        return InMemoryVectorStore()
    
    logger.info("Using Qdrant vector store")
    return QdrantVectorStore()
