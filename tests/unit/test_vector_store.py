"""
Unit Tests: Vector Store.

Tests for services/rag_service/core/vector_store.py.
"""

import pytest


class TestInMemoryVectorStore:
    """Tests for in-memory vector store."""
    
    @pytest.mark.asyncio
    async def test_add_document(self):
        """Add document to store."""
        from services.rag_service.core.vector_store import InMemoryVectorStore, Document
        
        store = InMemoryVectorStore()
        
        doc = Document(id="doc-1", content="Test content", metadata={"key": "value"})
        ids = await store.add([doc])
        
        assert ids == ["doc-1"]
    
    @pytest.mark.asyncio
    async def test_get_document(self):
        """Get document by ID."""
        from services.rag_service.core.vector_store import InMemoryVectorStore, Document
        
        store = InMemoryVectorStore()
        
        doc = Document(id="doc-2", content="Test content 2")
        await store.add([doc])
        
        results = await store.get(["doc-2"])
        
        assert len(results) == 1
        assert results[0].content == "Test content 2"
    
    @pytest.mark.asyncio
    async def test_search_basic(self):
        """Search with text matching."""
        from services.rag_service.core.vector_store import InMemoryVectorStore, Document
        
        store = InMemoryVectorStore()
        
        await store.add([
            Document(id="d1", content="Python programming language"),
            Document(id="d2", content="JavaScript web development"),
            Document(id="d3", content="Python data science"),
        ])
        
        results = await store.search("Python", limit=5)
        
        assert len(results) == 2
        assert all("Python" in r.content for r in results)
    
    @pytest.mark.asyncio
    async def test_delete_document(self):
        """Delete document from store."""
        from services.rag_service.core.vector_store import InMemoryVectorStore, Document
        
        store = InMemoryVectorStore()
        
        await store.add([Document(id="d-del", content="To delete")])
        await store.delete(["d-del"])
        
        results = await store.get(["d-del"])
        assert len(results) == 0


class TestVectorStoreFactory:
    """Tests for vector store factory."""
    
    def test_create_memory_store(self):
        """Create in-memory store."""
        from services.rag_service.core.vector_store import create_vector_store
        
        store = create_vector_store(use_memory=True)
        
        assert store is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
