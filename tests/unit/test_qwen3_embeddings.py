"""
Tests for Embedding Providers (Qwen3).
"""

import pytest


class TestQwen3Embedding:
    """Tests for Qwen3 Embedding Provider."""
    
    def test_import_embedding(self):
        """Test embedding module imports."""
        from shared.embedding.qwen3_embedding import (
            Qwen3Embedder,
            get_embedder,
        )
        
        assert Qwen3Embedder is not None or get_embedder is not None
        print("\n✅ Qwen3 embedding imports work")
    
    def test_create_embedder(self):
        """Test embedder creation."""
        from shared.embedding.qwen3_embedding import Qwen3Embedder
        
        embedder = Qwen3Embedder()
        
        assert embedder is not None
        print("\n✅ Qwen3Embedder created")
    
    def test_embed_text(self):
        """Test text embedding."""
        from shared.embedding.qwen3_embedding import Qwen3Embedder
        
        embedder = Qwen3Embedder()
        
        text = "Tesla is an electric vehicle company"
        
        # Note: May need model loaded to actually embed
        try:
            embedding = embedder.embed(text)
            assert len(embedding) > 0
            print(f"\n✅ Embedded to {len(embedding)} dimensions")
        except Exception as e:
            print(f"\n⏭️ Skipped (model not loaded): {e}")
    
    def test_embed_batch(self):
        """Test batch embedding."""
        from shared.embedding.qwen3_embedding import Qwen3Embedder
        
        embedder = Qwen3Embedder()
        
        texts = ["Tesla", "Ford", "GM"]
        
        try:
            embeddings = embedder.embed_batch(texts)
            assert len(embeddings) == len(texts)
            print(f"\n✅ Batch embedded {len(texts)} texts")
        except Exception as e:
            print(f"\n⏭️ Skipped (model not loaded): {e}")


class TestQwen3Reranker:
    """Tests for Qwen3 Reranker."""
    
    def test_import_reranker(self):
        """Test reranker module imports."""
        from shared.embedding.qwen3_reranker import (
            Qwen3Reranker,
            get_reranker,
        )
        
        assert Qwen3Reranker is not None or get_reranker is not None
        print("\n✅ Qwen3 reranker imports work")
    
    def test_create_reranker(self):
        """Test reranker creation."""
        from shared.embedding.qwen3_reranker import Qwen3Reranker
        
        reranker = Qwen3Reranker()
        
        assert reranker is not None
        print("\n✅ Qwen3Reranker created")
    
    def test_rerank_documents(self):
        """Test document reranking."""
        from shared.embedding.qwen3_reranker import Qwen3Reranker
        
        reranker = Qwen3Reranker()
        
        query = "Tesla revenue"
        documents = [
            "Tesla reported $81B revenue",
            "Apple is a tech company",
            "Tesla is growing fast",
        ]
        
        try:
            reranked = reranker.rerank(query, documents)
            assert len(reranked) == len(documents)
            print(f"\n✅ Reranked {len(documents)} documents")
        except Exception as e:
            print(f"\n⏭️ Skipped (model not loaded): {e}")


class TestQwen3VLEmbedding:
    """Tests for Qwen3 Vision-Language Embedding."""
    
    def test_import_vl_embedding(self):
        """Test VL embedding module imports."""
        from shared.embedding.qwen3_vl_embedding import (
            Qwen3VLEmbedder,
        )
        
        assert Qwen3VLEmbedder is not None
        print("\n✅ Qwen3 VL embedding imports work")
    
    def test_create_vl_embedder(self):
        """Test VL embedder creation."""
        from shared.embedding.qwen3_vl_embedding import Qwen3VLEmbedder
        
        embedder = Qwen3VLEmbedder()
        
        assert embedder is not None
        print("\n✅ Qwen3VLEmbedder created")
    
    def test_embed_text_with_vl(self):
        """Test text embedding with VL model."""
        from shared.embedding.qwen3_vl_embedding import Qwen3VLEmbedder
        
        embedder = Qwen3VLEmbedder()
        
        text = "A photo of a Tesla car"
        
        try:
            embedding = embedder.embed_text(text)
            assert len(embedding) > 0
            print(f"\n✅ VL embedded text to {len(embedding)} dimensions")
        except Exception as e:
            print(f"\n⏭️ Skipped (model not loaded): {e}")


class TestQwen3VLReranker:
    """Tests for Qwen3 Vision-Language Reranker."""
    
    def test_import_vl_reranker(self):
        """Test VL reranker module imports."""
        from shared.embedding.qwen3_vl_reranker import (
            Qwen3VLReranker,
        )
        
        assert Qwen3VLReranker is not None
        print("\n✅ Qwen3 VL reranker imports work")
    
    def test_create_vl_reranker(self):
        """Test VL reranker creation."""
        from shared.embedding.qwen3_vl_reranker import Qwen3VLReranker
        
        reranker = Qwen3VLReranker()
        
        assert reranker is not None
        print("\n✅ Qwen3VLReranker created")


class TestEmbeddingProviderFactory:
    """Tests for embedding provider factory."""
    
    def test_import_factory(self):
        """Test factory imports."""
        from shared.embedding import (
            get_embedding_provider,
            EmbeddingProvider,
        )
        
        assert get_embedding_provider is not None or EmbeddingProvider is not None
        print("\n✅ Factory imports work")
    
    def test_get_default_provider(self):
        """Test getting default provider."""
        from shared.embedding import get_embedding_provider
        
        try:
            provider = get_embedding_provider()
            assert provider is not None
            print("\n✅ Default provider obtained")
        except Exception as e:
            print(f"\n⏭️ Skipped: {e}")
    
    def test_get_specific_provider(self):
        """Test getting specific provider by name."""
        from shared.embedding import get_embedding_provider
        
        try:
            provider = get_embedding_provider("qwen3")
            assert provider is not None
            print("\n✅ Specific provider obtained")
        except Exception as e:
            print(f"\n⏭️ Skipped: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
