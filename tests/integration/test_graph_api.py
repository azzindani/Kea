"""
Integration Tests: Graph API.

Tests for /api/v1/graph/* endpoints.
"""

import pytest
import httpx


API_URL = "http://localhost:8080"


class TestGraphAPI:
    """Tests for Provenance Graph API endpoints."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_entities(self):
        """List graph entities."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/graph/entities")
        
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_entity(self):
        """Get entity by ID."""
        # This may return 404 if no entities exist, which is valid
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/graph/entities/test-entity")
        
        assert response.status_code in [200, 404]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_entity_provenance(self):
        """Get entity provenance graph."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{API_URL}/api/v1/graph/entities/test-entity/provenance",
                params={"depth": 2}
            )
        
        assert response.status_code in [200, 404]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_find_contradictions(self):
        """Find contradicting facts."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/graph/contradictions")
        
        assert response.status_code == 200
        data = response.json()
        assert "contradictions" in data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_graph_stats(self):
        """Get graph statistics."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/graph/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_entities" in data
        assert "total_facts" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
