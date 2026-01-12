"""
Integration Tests: Memory API.

Tests for /api/v1/memory/* endpoints.
Actual routes (from memory.py):
- POST /search - Semantic search
- GET /facts/{fact_id} - Get fact by ID
- GET /graph - Get provenance graph
- GET /sessions - List sessions
- GET /sessions/{id} - Get session
"""

import pytest
import httpx


API_URL = "http://localhost:8080"


class TestMemoryAPI:
    """Tests for Memory API endpoints."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_search_facts(self):
        """Search facts by query (POST method)."""
        async with httpx.AsyncClient(timeout=30) as client:
            # Note: API uses POST for search, not GET
            response = await client.post(
                f"{API_URL}/api/v1/memory/search",
                json={"query": "test query", "limit": 10}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data or "query" in data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_fact(self):
        """Get fact by ID (returns 404 for non-existent)."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{API_URL}/api/v1/memory/facts/nonexistent-id")
        
        # Expected: 404 since fact doesn't exist (placeholder implementation)
        assert response.status_code == 404
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_provenance_graph(self):
        """Get provenance graph."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/memory/graph")
        
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_sessions(self):
        """List research sessions."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/memory/sessions")
        
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
