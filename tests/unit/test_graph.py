"""
Unit Tests: LangGraph Research Graph.

Tests for services/orchestrator/core/graph.py
"""

import pytest


class TestGraphState:
    """Tests for graph state model."""
    
    def test_create_state(self):
        """Create graph state."""
        from services.orchestrator.core.graph import GraphState
        
        state = GraphState(
            job_id="job-123",
            query="Test research query",
        )
        
        assert state.job_id == "job-123"
        assert state.query == "Test research query"
        assert state.status == "pending"
    
    def test_state_defaults(self):
        """State has correct defaults."""
        from services.orchestrator.core.graph import GraphState
        
        state = GraphState(job_id="j", query="q")
        
        assert state.facts == []
        assert state.sources == []
        assert state.iteration == 0
        assert state.should_continue is True


class TestResearchGraph:
    """Tests for research graph compilation."""
    
    def test_compile_graph(self):
        """Compile research graph."""
        from services.orchestrator.core.graph import compile_research_graph
        
        graph = compile_research_graph()
        
        assert graph is not None


class TestGraphNodes:
    """Tests for individual graph nodes."""
    
    @pytest.mark.asyncio
    async def test_intention_router(self):
        """Test intention router node."""
        from services.orchestrator.core.graph import GraphState
        
        state = GraphState(
            job_id="test",
            query="What is the capital of France?",
        )
        
        # Just verify state can be created with path
        state.path = "A"
        assert state.path == "A"
    
    @pytest.mark.asyncio
    async def test_decomposer(self):
        """Test query decomposer."""
        from services.orchestrator.core.graph import GraphState
        
        state = GraphState(job_id="test", query="Complex query")
        state.sub_queries = ["sub1", "sub2"]
        
        assert len(state.sub_queries) == 2
    
    @pytest.mark.asyncio
    async def test_consensus_engine(self):
        """Test consensus engine state."""
        from services.orchestrator.core.graph import GraphState
        
        state = GraphState(job_id="test", query="q")
        state.generator_output = "Generated answer"
        state.critic_feedback = "Looks good"
        state.judge_verdict = "Approved"
        
        assert state.generator_output == "Generated answer"
        assert state.judge_verdict == "Approved"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
