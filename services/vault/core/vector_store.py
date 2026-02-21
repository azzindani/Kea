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

from shared.logging.main import get_logger


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
        limit: int = 100000,
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
        limit: int = 100000,
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
    
    Priority:
    1. Memory (if requested)
    2. PostgreSQL (pgvector) -> ONLY supported DB
    
    Args:
        use_memory: Use in-memory store instead of DB
        
    Returns:
        VectorStore instance
    """
    from shared.config import get_settings
    settings = get_settings()
    
    if use_memory:
        logger.info("Using in-memory vector store (requested)")
        return InMemoryVectorStore()
        
    # Check for Postgres (The Only Database)
    if settings.database.url:
        try:
            from services.vault.core.postgres_store import PostgresVectorStore
            logger.info("Using PostgreSQL vector store (pgvector)")
            return PostgresVectorStore()
        except ImportError as e:
            logger.error(f"Failed to import postgres_store: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize PostgresVectorStore: {e}")
            raise
            
    # Default fallback if no DB configured
    logger.warning("DATABASE_URL not set in centralized settings. Falling back to in-memory store (Data will be lost on restart)")
    return InMemoryVectorStore()

