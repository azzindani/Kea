"""
Unit Tests: LLM Client.

Tests for shared/llm/* - using actual API
"""

import pytest


class TestOpenRouterClient:
    """Tests for OpenRouter LLM client."""
    
    def test_init(self):
        """Initialize OpenRouter provider."""
        import os
        from shared.llm import OpenRouterProvider
        
        # Set dummy key if not set
        if not os.getenv("OPENROUTER_API_KEY"):
            os.environ["OPENROUTER_API_KEY"] = "test-key"
        
        provider = OpenRouterProvider()
        
        assert provider is not None
    
    def test_default_model(self):
        """Provider has default model."""
        import os
        from shared.llm import OpenRouterProvider
        
        if not os.getenv("OPENROUTER_API_KEY"):
            os.environ["OPENROUTER_API_KEY"] = "test-key"
        
        provider = OpenRouterProvider()
        
        assert provider.model is not None


class TestLLMResponse:
    """Tests for LLM response model."""
    
    def test_chat_response(self):
        """Create LLM response."""
        from shared.llm import LLMResponse
        
        response = LLMResponse(
            content="Hello, world!",
            model="test-model",
        )
        
        assert response.content == "Hello, world!"
        assert response.model == "test-model"


class TestFactory:
    """Tests for LLM factory."""
    
    def test_create_llm_provider(self):
        """Create LLM provider using constructor."""
        import os
        from shared.llm import OpenRouterProvider
        
        if not os.getenv("OPENROUTER_API_KEY"):
            os.environ["OPENROUTER_API_KEY"] = "test-key"
        
        provider = OpenRouterProvider()
        
        assert provider is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
