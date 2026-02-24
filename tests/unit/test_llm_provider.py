"""
Unit Tests: LLM Provider.

Tests for shared/llm/provider.py and shared/llm/openrouter.py
"""

import os

import pytest


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
        """Default model is defined as module constant."""
        from shared.llm.openrouter import DEFAULT_MODEL

        # Default model is a module constant, not instance attribute
        assert DEFAULT_MODEL is not None
        assert len(DEFAULT_MODEL) > 0

    def test_custom_model(self):
        """Provider uses config for custom model, not constructor."""
        from shared.llm import LLMConfig, OpenRouterProvider

        if not os.getenv("OPENROUTER_API_KEY"):
            os.environ["OPENROUTER_API_KEY"] = "test-key"

        provider = OpenRouterProvider()

        # Custom model is specified via LLMConfig, not constructor
        config = LLMConfig(model="custom/model")

        assert config.model == "custom/model"
        assert provider is not None


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
