"""
Simulation Tests: Research Flow.

End-to-end simulation tests for Colab/Kaggle.
"""

import pytest
import asyncio


class TestResearchSimulation:
    """Tests for complete research simulation."""
    
    @pytest.mark.simulation
    @pytest.mark.asyncio
    async def test_simple_research_flow(self):
        """Simulate simple research query."""
        from shared.schemas import JobRequest, JobType
        
        request = JobRequest(
            query="What is the capital of France?",
            job_type=JobType.QUICK_ANSWER,
            max_depth=1,
        )
        
        assert request.query == "What is the capital of France?"
        assert request.job_type == JobType.QUICK_ANSWER
    
    @pytest.mark.simulation
    @pytest.mark.asyncio
    async def test_deep_research_flow(self):
        """Simulate deep research query."""
        from shared.schemas import JobRequest, JobType, ResearchState, ResearchStatus
        
        # Create request
        request = JobRequest(
            query="Compare nickel production between Indonesia and Philippines",
            job_type=JobType.DEEP_RESEARCH,
            max_depth=3,
            max_sources=10,
        )
        
        # Create initial state
        state = ResearchState(
            job_id="sim-job-001",
            query=request.query,
        )
        
        # Simulate state progression
        state.status = ResearchStatus.RUNNING
        state.path = "D"  # Multi-source research
        state.sub_queries = [
            "Indonesia nickel production statistics",
            "Philippines nickel production statistics",
        ]
        
        # Simulate tool invocations
        state.tool_invocations.append({
            "tool_name": "web_search",
            "arguments": {"query": state.sub_queries[0]},
            "status": "success",
        })
        
        # Simulate fact extraction
        from shared.schemas import AtomicFact
        
        fact = AtomicFact(
            fact_id="sim-fact-001",
            entity="Indonesia",
            attribute="nickel_production",
            value="1.6 million tons",
            source_url="https://example.com",
            confidence_score=0.9,
        )
        
        state.facts.append(fact)
        
        # Simulate source tracking
        from shared.schemas import Source
        
        source = Source(
            url="https://example.com/report",
            title="Mining Report 2024",
            domain="example.com",
        )
        
        state.sources.append(source)
        
        # Verify state
        assert state.status == ResearchStatus.RUNNING
        assert len(state.facts) == 1
        assert len(state.sources) == 1
        assert state.path == "D"
    
    @pytest.mark.simulation
    @pytest.mark.asyncio
    async def test_consensus_simulation(self):
        """Simulate consensus engine."""
        from shared.schemas import ResearchState, ResearchStatus
        
        state = ResearchState(job_id="consensus-sim", query="test")
        
        # Simulate Generator
        state.generator_output = """
        Based on the collected facts:
        - Indonesia produced 1.6M tons of nickel in 2024
        - Philippines produced 0.4M tons in 2024
        
        Indonesia leads by 4x in production volume.
        """
        
        # Simulate Critic
        state.critic_feedback = """
        The analysis is accurate but could include:
        - Year-over-year growth rates
        - Market share percentages
        """
        
        # Simulate Judge
        state.judge_verdict = "Approved with minor suggestions"
        state.confidence = 0.85
        
        # Finalize
        state.status = ResearchStatus.COMPLETED
        state.report = state.generator_output
        
        assert state.confidence >= 0.8
        assert state.status == ResearchStatus.COMPLETED


class TestEmbeddingSimulation:
    """Tests for embedding simulation."""
    
    @pytest.mark.simulation
    def test_embedding_provider_selection(self):
        """Test embedding provider selection."""
        from shared.embedding import create_embedding_provider
        
        # API provider
        api_provider = create_embedding_provider(use_local=False)
        assert api_provider.dimension == 1024
        
        # Local provider
        local_provider = create_embedding_provider(use_local=True)
        assert local_provider.dimension == 1024


class TestGraphRAGSimulation:
    """Tests for GraphRAG simulation."""
    
    @pytest.mark.simulation
    def test_knowledge_graph_building(self):
        """Simulate building knowledge graph."""
        from services.rag_service.core.graph_rag import GraphRAG
        
        graph = GraphRAG()
        
        # Add entities
        indonesia = graph.add_entity("Indonesia", {"type": "country"})
        philippines = graph.add_entity("Philippines", {"type": "country"})
        nickel = graph.add_entity("Nickel", {"type": "commodity"})
        
        # Add facts
        graph.add_fact(indonesia, "nickel_production", "1.6M tons", "https://src1.com")
        graph.add_fact(philippines, "nickel_production", "0.4M tons", "https://src2.com")
        
        # Add relationships
        graph.add_relation(indonesia, nickel, "produces")
        graph.add_relation(philippines, nickel, "produces")
        
        # Query graph
        stats = graph.stats()
        
        assert stats["total_nodes"] >= 3
        assert stats["total_edges"] >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "simulation"])
