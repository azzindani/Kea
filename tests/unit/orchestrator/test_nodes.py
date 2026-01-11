"""
Unit Tests: Orchestrator Nodes.

Tests for services/orchestrator/nodes/*.py
"""

import pytest


class TestPlannerNode:
    """Tests for planner node."""
    
    @pytest.mark.asyncio
    async def test_planner_basic(self):
        """Planner decomposes query."""
        from services.orchestrator.nodes.planner import planner_node
        
        state = {"query": "Test research query"}
        result = await planner_node(state)
        
        assert "sub_queries" in result
        assert "status" in result
    
    @pytest.mark.asyncio
    async def test_planner_empty_query(self):
        """Planner handles empty query."""
        from services.orchestrator.nodes.planner import planner_node
        
        state = {"query": ""}
        result = await planner_node(state)
        
        assert "sub_queries" in result


class TestKeeperNode:
    """Tests for keeper node."""
    
    @pytest.mark.asyncio
    async def test_keeper_continue(self):
        """Keeper allows continuation."""
        from services.orchestrator.nodes.keeper import keeper_node
        
        state = {
            "query": "test",
            "facts": [],
            "iteration": 0,
            "max_iterations": 3,
        }
        result = await keeper_node(state)
        
        assert result.get("should_continue") == True
        assert result.get("iteration") == 1
    
    @pytest.mark.asyncio
    async def test_keeper_stop_max_iterations(self):
        """Keeper stops at max iterations."""
        from services.orchestrator.nodes.keeper import keeper_node
        
        state = {
            "query": "test",
            "facts": [],
            "iteration": 3,
            "max_iterations": 3,
        }
        result = await keeper_node(state)
        
        assert result.get("should_continue") == False


class TestSynthesizerNode:
    """Tests for synthesizer node."""
    
    @pytest.mark.asyncio
    async def test_synthesizer_basic(self):
        """Synthesizer generates report."""
        from services.orchestrator.nodes.synthesizer import synthesizer_node
        
        state = {
            "query": "Test query",
            "facts": [{"text": "Fact 1"}, {"text": "Fact 2"}],
            "sources": [{"url": "example.com"}],
        }
        result = await synthesizer_node(state)
        
        assert "report" in result
        assert result.get("status") == "complete"


class TestDivergenceNode:
    """Tests for divergence node."""
    
    @pytest.mark.asyncio
    async def test_divergence_basic(self):
        """Divergence generates alternatives."""
        from services.orchestrator.nodes.divergence import divergence_node
        
        state = {
            "query": "Test hypothesis",
            "hypotheses": ["H1", "H2"],
            "facts": [],
        }
        result = await divergence_node(state)
        
        assert result.get("divergence_complete") == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
