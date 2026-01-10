"""
Integration Tests: API Health.

Tests for all service health endpoints.
"""

import pytest
import httpx


# Base URLs for services
API_GATEWAY_URL = "http://localhost:8080"
ORCHESTRATOR_URL = "http://localhost:8000"
RAG_SERVICE_URL = "http://localhost:8001"


class TestAPIGatewayHealth:
    """Tests for API Gateway health."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test /health endpoint."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_GATEWAY_URL}/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_docs_available(self):
        """Test /docs endpoint."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_GATEWAY_URL}/docs")
        
        assert response.status_code == 200
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_openapi_json(self):
        """Test OpenAPI schema available."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_GATEWAY_URL}/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "paths" in data
        assert "info" in data


class TestOrchestratorHealth:
    """Tests for Orchestrator health."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test orchestrator health."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{ORCHESTRATOR_URL}/health")
        
        assert response.status_code == 200


class TestRAGServiceHealth:
    """Tests for RAG Service health."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test RAG service health."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{RAG_SERVICE_URL}/health")
        
        assert response.status_code == 200


class TestMetrics:
    """Tests for Prometheus metrics."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_metrics_endpoint(self):
        """Test /metrics endpoint."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_GATEWAY_URL}/metrics")
        
        assert response.status_code == 200
        # Prometheus format
        assert "python_info" in response.text or "process_" in response.text


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
