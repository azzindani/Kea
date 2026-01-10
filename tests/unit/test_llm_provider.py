"""
Unit Tests: LLM Provider.

Tests for shared/llm/provider.py and openrouter.py
"""

import pytest


class TestLLMProvider:
    """Tests for LLM provider base class."""
    
    def test_abstract_interface(self):
        """Provider interface has required methods."""
        from shared.llm.provider import LLMProvider
        
        # Verify abstract methods exist
        assert hasattr(LLMProvider, "complete")
        assert hasattr(LLMProvider, "chat")


class TestOpenRouterProvider:
    """Tests for OpenRouter provider."""
    
    def test_init(self):
        """Initialize provider."""
        from shared.llm.openrouter import OpenRouterProvider
        
        provider = OpenRouterProvider()
        
        assert provider.base_url == "https://openrouter.ai/api/v1"
    
    def test_default_model(self):
        """Default model is set."""
        from shared.llm.openrouter import OpenRouterProvider
        
        provider = OpenRouterProvider()
        
        assert provider.default_model is not None
    
    def test_custom_model(self):
        """Custom model can be set."""
        from shared.llm.openrouter import OpenRouterProvider
        
        provider = OpenRouterProvider(
            default_model="anthropic/claude-3-haiku"
        )
        
        assert provider.default_model == "anthropic/claude-3-haiku"


class TestLLMFactory:
    """Tests for LLM factory."""
    
    def test_create_provider(self):
        """Create LLM provider."""
        from shared.llm import create_llm_provider
        
        provider = create_llm_provider()
        
        assert provider is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
