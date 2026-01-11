"""
Unit Tests: Embedding Providers.

Tests for shared/embedding/*.py
"""

import pytest


class TestQwen3Embedding:
    """Tests for Qwen3 embedding."""
    
    def test_import(self):
        """Can import embedding."""
        from shared.embedding.qwen3_embedding import Qwen3Embedding
        
        assert Qwen3Embedding is not None


class TestQwen3Reranker:
    """Tests for Qwen3 reranker."""
    
    def test_import(self):
        """Can import reranker."""
        from shared.embedding.qwen3_reranker import Qwen3Reranker
        
        assert Qwen3Reranker is not None


class TestQwen3VLEmbedding:
    """Tests for Qwen3 VL embedding."""
    
    def test_import(self):
        """Can import VL embedding."""
        from shared.embedding.qwen3_vl_embedding import Qwen3VLEmbedding
        
        assert Qwen3VLEmbedding is not None


class TestQwen3VLReranker:
    """Tests for Qwen3 VL reranker."""
    
    def test_import(self):
        """Can import VL reranker."""
        from shared.embedding.qwen3_vl_reranker import Qwen3VLReranker
        
        assert Qwen3VLReranker is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
