"""
Unit Tests: Embedding Providers.

Tests for shared/embedding/*.py
"""

import pytest


class TestOpenRouterEmbedding:
    """Tests for OpenRouter embedding."""

    def test_init(self):
        """Initialize provider."""
        from shared.embedding import OpenRouterEmbedding

        provider = OpenRouterEmbedding(dimension=1024)

        assert provider.dimension == 1024
        assert provider.model == "qwen/qwen3-embedding-8b"

    def test_dimension_default(self):
        """Default dimension is 1024."""
        from shared.embedding import OpenRouterEmbedding

        provider = OpenRouterEmbedding()
        assert provider.dimension == 1024


class TestLocalEmbedding:
    """Tests for local embedding."""

    def test_init(self):
        """Initialize provider."""
        from shared.embedding import LocalEmbedding

        provider = LocalEmbedding(
            model_name="Qwen/Qwen3-Embedding-0.6B",
            dimension=512,
        )

        assert provider.dimension == 512
        assert provider.model_name == "Qwen/Qwen3-Embedding-0.6B"


class TestLocalReranker:
    """Tests for local reranker."""

    def test_init(self):
        """Initialize reranker."""
        from shared.embedding import LocalReranker

        reranker = LocalReranker(
            model_name="Qwen/Qwen3-Reranker-0.6B",
            max_length=4096,
        )

        assert reranker.max_length == 4096
        assert reranker.model_name == "Qwen/Qwen3-Reranker-0.6B"


class TestVLEmbedding:
    """Tests for vision-language embedding."""

    def test_init(self):
        """Initialize VL provider."""
        from shared.embedding import LocalVLEmbedding

        provider = LocalVLEmbedding(
            model_name="Qwen/Qwen3-VL-Embedding-2B",
        )

        assert provider.model_name == "Qwen/Qwen3-VL-Embedding-2B"


class TestFactory:
    """Tests for factory functions."""

    def test_create_api_embedding(self):
        """Create OpenRouter embedding."""
        from shared.embedding import create_embedding_provider

        provider = create_embedding_provider(use_local=False)

        from shared.embedding import OpenRouterEmbedding
        assert isinstance(provider, OpenRouterEmbedding)

    def test_create_local_embedding(self):
        """Create local embedding."""
        from shared.embedding import create_embedding_provider

        provider = create_embedding_provider(use_local=True)

        from shared.embedding import LocalEmbedding
        assert isinstance(provider, LocalEmbedding)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
