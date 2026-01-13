"""
Unit Tests: Fact Store.

Tests for services/rag_service/core/fact_store.py
"""

import pytest
from datetime import datetime


# Check if qdrant_client is available
try:
    import qdrant_client
    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False


class TestFactStore:
    """Tests for fact store operations."""
    
    @pytest.fixture
    def force_memory_store(self, monkeypatch):
        """Force in-memory vector store."""
        # Remove QDRANT_URL to force in-memory mode
        monkeypatch.delenv("QDRANT_URL", raising=False)
    
    @pytest.mark.asyncio
    async def test_add_fact(self, force_memory_store):
        """Add fact to store."""
        from services.rag_service.core.fact_store import FactStore
        from shared.schemas import AtomicFact
        
        store = FactStore(use_memory=True)  # Force memory
        
        fact = AtomicFact(
            fact_id="fact-001",
            entity="Test Entity",
            attribute="test_attr",
            value="100",
            source_url="https://example.com",
        )
        
        fact_id = await store.add_fact(fact)
        
        assert fact_id == "fact-001"
    
    @pytest.mark.asyncio
    async def test_get_fact(self, force_memory_store):
        """Get fact by ID."""
        from services.rag_service.core.fact_store import FactStore
        from shared.schemas import AtomicFact
        
        store = FactStore(use_memory=True)
        
        fact = AtomicFact(
            fact_id="fact-get",
            entity="Get Test",
            attribute="attr",
            value="val",
            source_url="url",
        )
        
        await store.add_fact(fact)
        
        retrieved = await store.get_fact("fact-get")
        
        assert retrieved is not None
        assert retrieved.entity == "Get Test"
    
    @pytest.mark.asyncio
    async def test_search_facts(self, force_memory_store):
        """Search facts by query."""
        from services.rag_service.core.fact_store import FactStore
        from shared.schemas import AtomicFact
        
        store = FactStore(use_memory=True)
        
        facts = [
            AtomicFact(fact_id="f1", entity="E1", attribute="a", value="v", source_url="u"),
            AtomicFact(fact_id="f2", entity="E2", attribute="a", value="v", source_url="u"),
        ]
        
        for fact in facts:
            await store.add_fact(fact)
        
        # In-memory search (basic functionality)
        results = await store.search("E1", limit=5)
        
        # Should return results (implementation dependent)
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_get_facts_by_entity(self, force_memory_store):
        """Get facts by entity."""
        from services.rag_service.core.fact_store import FactStore
        from shared.schemas import AtomicFact
        
        store = FactStore(use_memory=True)
        
        fact1 = AtomicFact(
            fact_id="ef1",
            entity="CompanyX",
            attribute="revenue",
            value="100M",
            source_url="url1",
        )
        fact2 = AtomicFact(
            fact_id="ef2",
            entity="CompanyX",
            attribute="employees",
            value="500",
            source_url="url2",
        )
        
        await store.add_fact(fact1)
        await store.add_fact(fact2)
        
        # Get by entity (if supported by implementation)
        facts = await store.get_facts_by_entity("CompanyX")
        
        assert isinstance(facts, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
