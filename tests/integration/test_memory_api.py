"""
Integration Tests: Memory API.

Tests for /api/v1/memory/* endpoints.
"""

import pytest
import httpx


API_URL = "http://localhost:8080"


class TestMemoryAPI:
    """Tests for Memory API endpoints."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_search_facts(self):
        """Search facts by query."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{API_URL}/api/v1/memory/search",
                params={"query": "test query", "limit": 10}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "facts" in data or "results" in data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_add_fact(self):
        """Add fact to memory."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{API_URL}/api/v1/memory/facts",
                json={
                    "entity": "Test Entity",
                    "attribute": "test_attr",
                    "value": "test_value",
                    "source_url": "https://example.com",
                }
            )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert "fact_id" in data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_fact(self):
        """Get fact by ID."""
        async with httpx.AsyncClient(timeout=30) as client:
            # Add first
            add_resp = await client.post(
                f"{API_URL}/api/v1/memory/facts",
                json={
                    "entity": "Get Test",
                    "attribute": "attr",
                    "value": "val",
                    "source_url": "url",
                }
            )
            
            if add_resp.status_code in [200, 201]:
                fact_id = add_resp.json()["fact_id"]
                
                # Get
                response = await client.get(f"{API_URL}/api/v1/memory/facts/{fact_id}")
                
                assert response.status_code == 200
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_entities(self):
        """List all entities."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/memory/entities")
        
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_entity_facts(self):
        """Get facts for an entity."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{API_URL}/api/v1/memory/entities/TestEntity/facts"
            )
        
        # May return 404 if entity doesn't exist
        assert response.status_code in [200, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
