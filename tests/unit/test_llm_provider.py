"""
Unit Tests: LLM Provider.

Tests for shared/llm/provider.py and shared/llm/openrouter.py
"""

import pytest
import os


class TestLLMProvider:
    """Tests for LLM provider abstract class."""
    
    def test_abstract_interface(self):
        """LLMProvider has required methods."""
        from shared.llm.provider import LLMProvider
        
        # Check for abstract methods
        assert hasattr(LLMProvider, "complete")
        assert hasattr(LLMProvider, "stream")
        assert hasattr(LLMProvider, "count_tokens")


class TestOpenRouterProvider:
    """Tests for OpenRouter provider."""
    
    def test_init(self):
        """Initialize provider."""
        from shared.llm import OpenRouterProvider
        
        if not os.getenv("OPENROUTER_API_KEY"):
            os.environ["OPENROUTER_API_KEY"] = "test-key"
        
        provider = OpenRouterProvider()
        
        assert provider is not None
    
    def test_default_model(self):
        """Provider has default model attribute."""
        from shared.llm import OpenRouterProvider
        
        if not os.getenv("OPENROUTER_API_KEY"):
            os.environ["OPENROUTER_API_KEY"] = "test-key"
        
        provider = OpenRouterProvider()
        
        # OpenRouterProvider uses 'model' attribute
        assert provider.model is not None
    
    def test_custom_model(self):
        """Provider accepts custom model."""
        from shared.llm import OpenRouterProvider
        
        if not os.getenv("OPENROUTER_API_KEY"):
            os.environ["OPENROUTER_API_KEY"] = "test-key"
        
        provider = OpenRouterProvider(model="custom/model")
        
        assert provider.model == "custom/model"


class TestLLMFactory:
    """Tests for LLM provider factory."""
    
    def test_create_provider(self):
        """Create provider directly."""
        from shared.llm import OpenRouterProvider
        
        if not os.getenv("OPENROUTER_API_KEY"):
            os.environ["OPENROUTER_API_KEY"] = "test-key"
        
        provider = OpenRouterProvider()
        
        assert provider is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
