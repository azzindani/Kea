"""
Unit Tests: Embedding Providers.

Tests for shared/embedding/*.py
"""

import pytest


class TestOpenRouterEmbedding:
    """Tests for OpenRouter embedding (API)."""

    def test_import(self):
        """Can import OpenRouter embedding."""
        from shared.embedding.qwen3_embedding import OpenRouterEmbedding

        assert OpenRouterEmbedding is not None


class TestLocalEmbedding:
    """Tests for local embedding."""

    def test_import(self):
        """Can import local embedding."""
        from shared.embedding.qwen3_embedding import LocalEmbedding

        assert LocalEmbedding is not None


class TestEmbeddingFactory:
    """Tests for embedding factory."""

    def test_factory_import(self):
        """Can import factory function."""
        from shared.embedding.qwen3_embedding import create_embedding_provider

        assert create_embedding_provider is not None


class TestRerankerImports:
    """Tests for reranker imports."""

    def test_reranker_module_exists(self):
        """Reranker module exists."""
        import importlib.util
        spec = importlib.util.find_spec("shared.embedding.qwen3_reranker")
        assert spec is not None, "qwen3_reranker module exists"


class TestVLEmbeddingImports:
    """Tests for VL embedding imports."""

    def test_vl_module_exists(self):
        """VL embedding module exists."""
        import importlib.util
        spec = importlib.util.find_spec("shared.embedding.qwen3_vl_embedding")
        assert spec is not None, "qwen3_vl_embedding module exists"


class TestVLRerankerImports:
    """Tests for VL reranker imports."""

    def test_vl_reranker_module_exists(self):
        """VL reranker module exists."""
        import importlib.util
        spec = importlib.util.find_spec("shared.embedding.qwen3_vl_reranker")
        assert spec is not None, "qwen3_vl_reranker module exists"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
