"""
Tests for LangGraph nodes (planner, divergence, keeper, synthesizer).
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestDivergenceNode:
    """Tests for divergence_node function."""
    
    def test_import_divergence(self):
        """Test that divergence node can be imported."""
        from services.orchestrator.nodes.divergence import divergence_node
        assert divergence_node is not None
    
    @pytest.mark.asyncio
    async def test_divergence_without_api_key(self):
        """Test divergence with no API key."""
        from services.orchestrator.nodes.divergence import divergence_node
        
        with patch.dict('os.environ', {}, clear=True):
            state = {
                "query": "Test query",
                "facts": ["Fact 1"],
                "hypotheses": ["Hypothesis 1"],
            }
            
            result = await divergence_node(state)
            
            assert result["divergence_complete"] is True
            assert "alternative_hypotheses" in result


class TestKeeperNode:
    """Tests for keeper_node function."""
    
    def test_import_keeper(self):
        """Test that keeper node can be imported."""
        from services.orchestrator.nodes.keeper import keeper_node
        assert keeper_node is not None
    
    @pytest.mark.asyncio
    async def test_keeper_stops_at_max_iterations(self):
        """Test keeper stops at max iterations."""
        from services.orchestrator.nodes.keeper import keeper_node
        
        state = {
            "query": "Test query",
            "iteration": 3,
            "max_iterations": 3,
            "facts": [],
        }
        
        result = await keeper_node(state)
        
        assert result["should_continue"] is False
    
    @pytest.mark.asyncio
    async def test_keeper_continues_when_needed(self):
        """Test keeper continues when more research needed."""
        from services.orchestrator.nodes.keeper import keeper_node
        
        state = {
            "query": "Test query",
            "iteration": 0,
            "max_iterations": 3,
            "facts": [],
        }
        
        result = await keeper_node(state)
        
        assert result["should_continue"] is True
        assert result["iteration"] == 1


class TestPlannerNode:
    """Tests for planner_node function."""
    
    def test_import_planner(self):
        """Test that planner node can be imported."""
        from services.orchestrator.nodes.planner import planner_node
        assert planner_node is not None
    
    @pytest.mark.asyncio
    async def test_planner_without_api_key(self):
        """Test planner uses query as-is without API key."""
        from services.orchestrator.nodes.planner import planner_node
        
        with patch.dict('os.environ', {}, clear=True):
            state = {"query": "What is machine learning?"}
            
            result = await planner_node(state)
            
            assert "sub_queries" in result
            assert result["sub_queries"] == ["What is machine learning?"]
            assert result["status"] == "planning_complete"


class TestSynthesizerNode:
    """Tests for synthesizer_node function."""
    
    def test_import_synthesizer(self):
        """Test that synthesizer node can be imported."""
        from services.orchestrator.nodes.synthesizer import synthesizer_node
        assert synthesizer_node is not None
    
    @pytest.mark.asyncio
    async def test_synthesizer_without_api_key(self):
        """Test synthesizer fallback without API key."""
        from services.orchestrator.nodes.synthesizer import synthesizer_node
        
        with patch.dict('os.environ', {}, clear=True):
            state = {
                "query": "Test query",
                "facts": ["Fact 1", "Fact 2"],
                "sources": ["Source 1"],
            }
            
            result = await synthesizer_node(state)
            
            assert "report" in result
            assert "confidence" in result
            assert result["status"] == "complete"
            assert "2" in result["report"]  # Facts count
