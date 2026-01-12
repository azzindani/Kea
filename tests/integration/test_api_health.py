"""
Integration Tests: API Health.

Tests for all service health endpoints.
These tests require the corresponding services to be running.
If a service is not running, the test will be skipped.
"""

import pytest
import httpx


# Base URLs for services
API_GATEWAY_URL = "http://localhost:8080"
ORCHESTRATOR_URL = "http://localhost:8000"
RAG_SERVICE_URL = "http://localhost:8001"


async def check_service_available(url: str) -> bool:
    """Check if a service is available."""
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            response = await client.get(f"{url}/health")
            return response.status_code == 200
    except Exception:
        return False


class TestAPIGatewayHealth:
    """Tests for API Gateway health."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test /health endpoint."""
        if not await check_service_available(API_GATEWAY_URL):
            pytest.skip(f"API Gateway not running at {API_GATEWAY_URL}")
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_GATEWAY_URL}/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_docs_available(self):
        """Test /docs endpoint."""
        if not await check_service_available(API_GATEWAY_URL):
            pytest.skip(f"API Gateway not running at {API_GATEWAY_URL}")
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_GATEWAY_URL}/docs")
        
        assert response.status_code == 200
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_openapi_json(self):
        """Test OpenAPI schema available."""
        if not await check_service_available(API_GATEWAY_URL):
            pytest.skip(f"API Gateway not running at {API_GATEWAY_URL}")
        
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
        if not await check_service_available(ORCHESTRATOR_URL):
            pytest.skip(f"Orchestrator not running at {ORCHESTRATOR_URL}")
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{ORCHESTRATOR_URL}/health")
        
        assert response.status_code == 200


class TestRAGServiceHealth:
    """Tests for RAG Service health."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test RAG service health."""
        if not await check_service_available(RAG_SERVICE_URL):
            pytest.skip(f"RAG Service not running at {RAG_SERVICE_URL}")
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{RAG_SERVICE_URL}/health")
        
        assert response.status_code == 200


class TestMetrics:
    """Tests for Prometheus metrics."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_metrics_endpoint(self):
        """Test /metrics endpoint."""
        if not await check_service_available(API_GATEWAY_URL):
            pytest.skip(f"API Gateway not running at {API_GATEWAY_URL}")
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_GATEWAY_URL}/metrics")
        
        assert response.status_code == 200
        # Prometheus format
        assert "python_info" in response.text or "process_" in response.text


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
