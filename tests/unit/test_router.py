"""
Tests for IntentionRouter.
"""

import pytest
from unittest.mock import patch, AsyncMock


class TestRouter:
    """Tests for IntentionRouter."""
    
    def test_import_router(self):
        """Test that router can be imported."""
        from services.orchestrator.core.router import IntentionRouter, PathType
        assert IntentionRouter is not None
    
    def test_create_router(self):
        """Test creating router instance."""
        from services.orchestrator.core.router import IntentionRouter
        router = IntentionRouter()
        assert router is not None
        assert router.system_prompt is not None
    
    @pytest.mark.asyncio
    async def test_route_returns_path(self):
        """Test route returns a valid path."""
        from services.orchestrator.core.router import IntentionRouter
        
        with patch.dict('os.environ', {}, clear=True):
            router = IntentionRouter()
            path = await router.route("What is AI?")
            
            assert path in ["A", "B", "C", "D"]
    
    @pytest.mark.asyncio
    async def test_route_complex_query(self):
        """Test routing complex query."""
        from services.orchestrator.core.router import IntentionRouter
        
        with patch.dict('os.environ', {}, clear=True):
            router = IntentionRouter()
            path = await router.route("Compare studies on climate change")
            
            # Should route to Path C (meta-analysis)
            assert path == "C"
    
    @pytest.mark.asyncio
    async def test_route_verification_query(self):
        """Test routing verification query."""
        from services.orchestrator.core.router import IntentionRouter
        
        with patch.dict('os.environ', {}, clear=True):
            router = IntentionRouter()
            path = await router.route("Verify the claims in this study")
            
            # Should route to Path B (verification)
            assert path == "B"
    
    def test_heuristic_route_meta_analysis(self):
        """Test heuristic routing for meta-analysis."""
        from services.orchestrator.core.router import IntentionRouter
        
        router = IntentionRouter()
        path = router._heuristic_route("meta-analysis of studies", None)
        
        assert path == "C"
    
    def test_heuristic_route_verify(self):
        """Test heuristic routing for verification."""
        from services.orchestrator.core.router import IntentionRouter
        
        router = IntentionRouter()
        path = router._heuristic_route("verify this data", None)
        
        assert path == "B"
    
    def test_heuristic_route_no_match(self):
        """Test heuristic returns None when no match."""
        from services.orchestrator.core.router import IntentionRouter
        
        router = IntentionRouter()
        path = router._heuristic_route("random question", None)
        
        assert path is None


class TestRouterNode:
    """Tests for router_node function."""
    
    def test_import_router_node(self):
        """Test router_node can be imported."""
        from services.orchestrator.core.router import router_node
        assert router_node is not None
    
    @pytest.mark.asyncio
    async def test_router_node_sets_path(self):
        """Test router_node sets path in state."""
        from services.orchestrator.core.router import router_node
        
        with patch.dict('os.environ', {}, clear=True):
            state = {"query": "Test query"}
            result = await router_node(state)
            
            assert "path" in result
            assert result["path"] in ["A", "B", "C", "D"]
