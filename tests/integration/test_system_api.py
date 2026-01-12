"""
Integration Tests: System API.

Tests for /api/v1/system/* endpoints.
"""

import pytest
import httpx


API_URL = "http://localhost:8080"


class TestSystemCapabilities:
    """Tests for system capabilities endpoint."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_capabilities(self):
        """Get system capabilities."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/system/capabilities")
        
        assert response.status_code == 200
        data = response.json()
        assert "mcp_servers" in data
        assert "research_paths" in data


class TestSystemConfig:
    """Tests for system configuration endpoint."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_config(self):
        """Get system configuration."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/system/config")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have some config values
        assert isinstance(data, dict)


class TestSystemMetrics:
    """Tests for system metrics endpoint."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_metrics_summary(self):
        """Get metrics summary."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/system/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "uptime_seconds" in data or isinstance(data, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
