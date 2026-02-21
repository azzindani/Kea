"""
RAG Service Client.

HTTP client for calling the RAG service.
"""

from __future__ import annotations

from typing import Any, Optional
import httpx

from shared.logging.main import get_logger
from shared.config import get_settings
from shared.service_registry import ServiceRegistry, ServiceName

logger = get_logger(__name__)


class RAGServiceClient:
    """
    HTTP client for the RAG service.
    
    Features:
    - Semantic search
    - Fact storage and retrieval
    - Artifact management
    - Knowledge graph queries
    
    Example:
        client = RAGServiceClient()
        results = await client.search("AI ethics", limit=10)
    """
    
    def __init__(self, base_url: str | None = None) -> None:
        settings = get_settings()
        self.base_url = base_url or ServiceRegistry.get_url(ServiceName.RAG_SERVICE)
        # Use centralized timeouts
        self.timeout = httpx.Timeout(
            settings.timeouts.default,
            connect=settings.timeouts.auth_token,
        )
    
    async def health_check(self) -> dict[str, Any]:
        """Check RAG service health."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
    
    async def search(
        self,
        query: str,
        limit: int | None = None,
        min_score: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Semantic search for facts.
        
        Args:
            query: Search query
            limit: Max results
            min_score: Minimum similarity score
            
        Returns:
            List of matching facts
        """
        settings = get_settings()
        limit = limit or settings.rag.default_limit
        min_score = min_score if min_score is not None else settings.rag.default_min_score
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/search",
                json={
                    "query": query,
                    "limit": limit,
                    "min_score": min_score,
                }
            )
            response.raise_for_status()
            return response.json().get("results", [])
    
    async def add_fact(self, fact: dict[str, Any]) -> str:
        """
        Add a fact to the store.
        
        Args:
            fact: Fact data with text, source, etc.
            
        Returns:
            Fact ID
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/facts",
                json=fact,
            )
            response.raise_for_status()
            return response.json().get("id", "")
    
    async def get_fact(self, fact_id: str) -> dict[str, Any] | None:
        """Get a fact by ID."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/facts/{fact_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
    
    async def store_artifact(
        self,
        name: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Store an artifact.
        
        Args:
            name: Artifact name
            content: Binary content
            content_type: MIME type
            
        Returns:
            Artifact ID
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/artifacts",
                files={"file": (name, content, content_type)},
            )
            response.raise_for_status()
            return response.json().get("id", "")
    
    async def get_artifact(self, artifact_id: str) -> bytes | None:
        """Get artifact content by ID."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/artifacts/{artifact_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.content
    
    async def query_graph(self, query: str) -> dict[str, Any]:
        """
        Query the knowledge graph.
        
        Args:
            query: Graph query
            
        Returns:
            Graph query results with nodes and edges
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/graph/query",
                json={"query": query},
            )
            response.raise_for_status()
            return response.json()


# Singleton
_client: Optional[RAGServiceClient] = None

async def get_rag_client() -> RAGServiceClient:
    """Get singleton client."""
    global _client
    if _client is None:
        _client = RAGServiceClient()
    return _client
