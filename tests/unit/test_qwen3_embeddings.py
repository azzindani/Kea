"""
Tests for Qwen3 embedding providers.
"""

from unittest.mock import patch

import pytest


class TestEmbeddingProvider:
    """Tests for EmbeddingProvider base class."""

    def test_import_embedding(self):
        """Test that embedding classes can be imported."""
        from shared.embedding.qwen3_embedding import (
            EmbeddingProvider,
            LocalEmbedding,
            OpenRouterEmbedding,
        )
        assert EmbeddingProvider is not None
        assert OpenRouterEmbedding is not None
        assert LocalEmbedding is not None


class TestOpenRouterEmbedding:
    """Tests for OpenRouterEmbedding."""

    def test_create_embedder(self):
        """Test creating OpenRouter embedding instance."""
        from shared.embedding.qwen3_embedding import OpenRouterEmbedding
        embedder = OpenRouterEmbedding(api_key="test_key", dimension=512)

        assert embedder.dimension == 512
        assert embedder.model == "qwen/qwen3-embedding-8b"

    def test_default_dimension(self):
        """Test default dimension."""
        from shared.embedding.qwen3_embedding import OpenRouterEmbedding
        embedder = OpenRouterEmbedding()

        assert embedder.dimension == 1024

    @pytest.mark.asyncio
    async def test_embed_requires_api_key(self):
        """Test that embed raises error without API key."""
        from shared.embedding.qwen3_embedding import OpenRouterEmbedding

        with patch.dict('os.environ', {}, clear=True):
            embedder = OpenRouterEmbedding(api_key="")

            with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
                await embedder.embed(["test text"])


class TestLocalEmbedding:
    """Tests for LocalEmbedding."""

    def test_create_local_embedder(self):
        """Test creating local embedding instance."""
        from shared.embedding.qwen3_embedding import LocalEmbedding
        embedder = LocalEmbedding(dimension=768)

        assert embedder.dimension == 768
        assert embedder._model is None  # Lazy loaded

    def test_default_model_name(self):
        """Test default model name."""
        from shared.embedding.qwen3_embedding import LocalEmbedding
        embedder = LocalEmbedding()

        assert "Qwen" in embedder.model_name


class TestCreateEmbeddingProvider:
    """Tests for create_embedding_provider factory."""

    def test_create_openrouter_provider(self):
        """Test creating OpenRouter provider."""
        from shared.embedding.qwen3_embedding import (
            OpenRouterEmbedding,
            create_embedding_provider,
        )

        provider = create_embedding_provider(use_local=False, dimension=512)
        assert isinstance(provider, OpenRouterEmbedding)
        assert provider.dimension == 512

    def test_create_local_provider(self):
        """Test creating local provider."""
        from shared.embedding.qwen3_embedding import (
            LocalEmbedding,
            create_embedding_provider,
        )

        provider = create_embedding_provider(use_local=True, dimension=768)
        assert isinstance(provider, LocalEmbedding)
        assert provider.dimension == 768
