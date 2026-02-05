"""
RAG Service Client.

HTTP client for calling the RAG service.
"""

from __future__ import annotations

from typing import Any
import httpx

from shared.logging import get_logger
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
        self.base_url = base_url or ServiceRegistry.get_url(ServiceName.RAG_SERVICE)
        self.timeout = httpx.Timeout(60.0, connect=10.0)
    
    async def health_check(self) -> dict[str, Any]:
        """Check RAG service health."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
    
    async def search(
        self,
        query: str,
        limit: int = 100000,
        min_score: float = 0.5,
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
