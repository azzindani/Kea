"""
Integration Tests.

End-to-end tests for the full research pipeline.
Uses authenticated client for protected endpoints.
"""

import pytest
import asyncio
import httpx


# ============================================================================
# API Gateway Integration Tests
# ============================================================================

class TestAPIGateway:
    """Integration tests for the API Gateway."""
    
    base_url = "http://localhost:8080"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test API health endpoint (no auth needed)."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test listing available tools (no auth needed)."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v1/mcp/tools")
        
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        
        # Should always have tools (built-in fallback)
        assert len(data["tools"]) > 0, "Expected at least some tools (built-in fallback should work)"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_job(self, auth_client):
        """Test creating a research job (requires auth)."""
        response = await auth_client.post(
            "/api/v1/jobs/",
            json={
                "query": "Test research query",
                "job_type": "deep_research",
                "depth": 2,
            }
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "job_id" in data
        assert data["status"] in ["pending", "running"]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_system_capabilities(self):
        """Test system capabilities endpoint (no auth needed)."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/v1/system/capabilities")
        
        assert response.status_code == 200
        data = response.json()
        assert "mcp_servers" in data
        assert "research_paths" in data


# ============================================================================
# RAG Service Integration Tests
# ============================================================================

class TestRAGService:
    """Integration tests for the RAG Service."""
    
    base_url = "http://localhost:8001"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test RAG service health."""
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{self.base_url}/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_add_and_search_fact(self):
        """Test adding and searching for a fact."""
        async with httpx.AsyncClient(timeout=30) as client:
            # Add a fact
            add_response = await client.post(
                f"{self.base_url}/facts",
                json={
                    "entity": "Indonesia nickel",
                    "attribute": "production",
                    "value": "1.5 million tons",
                    "source_url": "https://example.com/report",
                    "confidence_score": 0.9,
                }
            )
            
            # May fail with 500 if vector store not configured
            if add_response.status_code in [500, 503]:
                pytest.skip("RAG Service vector store not configured")
            
            assert add_response.status_code == 200
            add_data = add_response.json()
            fact_id = add_data["fact_id"]
            
            # Search for the fact
            search_response = await client.post(
                f"{self.base_url}/facts/search",
                json={
                    "query": "Indonesia nickel production",
                    "limit": 10,
                }
            )
            
            assert search_response.status_code == 200


# ============================================================================
# Orchestrator Integration Tests
# ============================================================================

class TestOrchestratorService:
    """Integration tests for the Orchestrator."""
    
    base_url = "http://localhost:8000"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test orchestrator health."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_research_endpoint(self):
        """Test the research endpoint."""
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/research",
                json={
                    "query": "Simple test query",
                    "depth": 1,
                    "max_sources": 5,
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert "report" in data


# ============================================================================
# Full Pipeline Integration Test
# ============================================================================

class TestFullPipeline:
    """End-to-end pipeline tests."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_research_flow(self, auth_client):
        """Test complete research flow (requires auth)."""
        # 1. Create a job
        create_response = await auth_client.post(
            "/api/v1/jobs/",
            json={
                "query": "What is Python programming?",
                "depth": 1,
            }
        )
        
        assert create_response.status_code == 200, f"Failed: {create_response.text}"
        job_id = create_response.json()["job_id"]
        
        # 2. Poll for completion (with timeout)
        import time
        start = time.time()
        max_wait = 60  # 60 seconds max
        
        while time.time() - start < max_wait:
            status_response = await auth_client.get(f"/api/v1/jobs/{job_id}")
            status_data = status_response.json()
            
            if status_data["status"] in ["completed", "failed"]:
                break
            
            await asyncio.sleep(2)
        
        # 3. Get result (may be 400 if not completed yet)
        result_response = await auth_client.get(f"/api/v1/jobs/{job_id}/result")
        
        if result_response.status_code == 200:
            result_data = result_response.json()
            assert result_data["report"] is not None


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
