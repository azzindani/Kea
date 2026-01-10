"""
Unit Tests: LLM Client.

Tests for shared/llm/client.py
"""

import pytest


class TestOpenRouterClient:
    """Tests for OpenRouter LLM client."""
    
    def test_init(self):
        """Initialize client."""
        from shared.llm.client import OpenRouterClient
        
        client = OpenRouterClient()
        
        assert client.base_url == "https://openrouter.ai/api/v1"
    
    def test_default_model(self):
        """Default model is set."""
        from shared.llm.client import OpenRouterClient
        
        client = OpenRouterClient()
        
        assert client.default_model is not None


class TestLLMResponse:
    """Tests for LLM response models."""
    
    def test_chat_response(self):
        """Create chat response."""
        from shared.llm.client import ChatResponse
        
        response = ChatResponse(
            content="Hello!",
            model="test-model",
            usage={"prompt_tokens": 10, "completion_tokens": 5},
        )
        
        assert response.content == "Hello!"
        assert response.usage["prompt_tokens"] == 10


class TestFactory:
    """Tests for factory functions."""
    
    def test_create_llm_client(self):
        """Create LLM client via factory."""
        from shared.llm import create_llm_client
        
        client = create_llm_client()
        
        assert client is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
