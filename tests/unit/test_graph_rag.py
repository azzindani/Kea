"""
Unit Tests: GraphRAG.

Tests for services/rag_service/core/graph_rag.py.
"""

import pytest


class TestGraphRAG:
    """Tests for GraphRAG knowledge graph."""
    
    def test_add_entity(self):
        """Add entity to graph."""
        from services.rag_service.core.graph_rag import GraphRAG
        
        graph = GraphRAG()
        
        entity_id = graph.add_entity("Indonesia Nickel", {"type": "commodity"})
        
        assert entity_id is not None
        assert entity_id.startswith("entity-")
    
    def test_add_duplicate_entity(self):
        """Adding same entity returns same ID."""
        from services.rag_service.core.graph_rag import GraphRAG
        
        graph = GraphRAG()
        
        id1 = graph.add_entity("Test Entity")
        id2 = graph.add_entity("Test Entity")
        
        assert id1 == id2
    
    def test_add_fact(self):
        """Add fact connected to entity."""
        from services.rag_service.core.graph_rag import GraphRAG
        
        graph = GraphRAG()
        
        entity_id = graph.add_entity("Nickel")
        fact_id = graph.add_fact(
            entity_id,
            attribute="production",
            value="1.5M tons",
            source_url="https://example.com",
        )
        
        assert fact_id.startswith("fact-")
    
    def test_get_entity_facts(self):
        """Get all facts for an entity."""
        from services.rag_service.core.graph_rag import GraphRAG
        
        graph = GraphRAG()
        
        entity_id = graph.add_entity("Test")
        graph.add_fact(entity_id, "attr1", "val1", "url1")
        graph.add_fact(entity_id, "attr2", "val2", "url2")
        
        facts = graph.get_entity_facts(entity_id)
        
        assert len(facts) == 2
    
    def test_find_contradictions(self):
        """Find contradicting facts."""
        from services.rag_service.core.graph_rag import GraphRAG
        
        graph = GraphRAG()
        
        entity_id = graph.add_entity("Company")
        # Same attribute, different values
        graph.add_fact(entity_id, "revenue", "100M", "url1")
        graph.add_fact(entity_id, "revenue", "150M", "url2")
        
        contradictions = graph.find_contradictions(entity_id)
        
        assert len(contradictions) >= 1
    
    def test_get_provenance_path(self):
        """Get provenance graph."""
        from services.rag_service.core.graph_rag import GraphRAG
        
        graph = GraphRAG()
        
        entity_id = graph.add_entity("Test Entity")
        graph.add_fact(entity_id, "test", "value", "https://source.com")
        
        provenance = graph.get_provenance_path(entity_id)
        
        assert "nodes" in provenance
        assert "edges" in provenance
        assert len(provenance["nodes"]) >= 1
    
    def test_graph_stats(self):
        """Get graph statistics."""
        from services.rag_service.core.graph_rag import GraphRAG
        
        graph = GraphRAG()
        
        graph.add_entity("E1")
        graph.add_entity("E2")
        
        stats = graph.stats()
        
        assert stats["total_nodes"] == 2
        assert "nodes_by_type" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
