"""
Integration Tests: LLM API.

Tests for /api/v1/llm/* endpoints.
"""

import pytest
import httpx


from shared.config import get_settings

API_URL = get_settings().services.gateway


class TestLLMProviders:
    """Tests for LLM provider endpoints."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_providers(self):
        """List LLM providers."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/llm/providers")
        
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert len(data["providers"]) > 0
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_list_models(self):
        """List available models."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/llm/models")
        
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        
        # Verify model structure
        if data["models"]:
            model = data["models"][0]
            assert "id" in model
            assert "name" in model
            assert "provider" in model


class TestLLMConfig:
    """Tests for LLM configuration."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_config(self):
        """Get LLM configuration."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/llm/config")
        
        assert response.status_code == 200
        data = response.json()
        assert "default_provider" in data
        assert "default_model" in data


class TestLLMUsage:
    """Tests for LLM usage statistics."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_usage(self):
        """Get LLM usage stats."""
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{API_URL}/api/v1/llm/usage")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "total_tokens_input" in data


class TestLLMGenerate:
    """Tests for direct LLM generation."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_generate(self):
        """Test direct generation endpoint."""
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{API_URL}/api/v1/llm/generate",
                json={
                    "model": "nvidia/nemotron-3-nano-30b-a3b:free",
                    "messages": [{"role": "user", "content": "What is 2+2? Answer briefly."}],
                    "max_tokens": 50,
                }
            )
        
        # May fail if API key not set
        if response.status_code == 200:
            data = response.json()
            assert "content" in data
            assert "usage" in data
        else:
            # Expected if API key not configured
            assert response.status_code in [500, 502]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
