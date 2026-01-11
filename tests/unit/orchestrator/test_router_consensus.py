"""
Unit Tests: Router and Consensus.

Tests for services/orchestrator/core/router.py and consensus.py
"""

import pytest


class TestIntentionRouter:
    """Tests for intention router."""
    
    def test_router_init(self):
        """Router initializes correctly."""
        from services.orchestrator.core.router import IntentionRouter
        
        router = IntentionRouter()
        
        assert router.system_prompt is not None
    
    @pytest.mark.asyncio
    async def test_router_path_c_heuristic(self):
        """Router detects meta-analysis (Path C)."""
        from services.orchestrator.core.router import IntentionRouter
        
        router = IntentionRouter()
        
        query = "Compare different studies on climate change"
        path = await router.route(query)
        
        # C for compare/meta-analysis
        assert path in ["C", "D"]
    
    @pytest.mark.asyncio
    async def test_router_path_b_heuristic(self):
        """Router detects verification (Path B)."""
        from services.orchestrator.core.router import IntentionRouter
        
        router = IntentionRouter()
        
        query = "Verify the claim that X is true"
        path = await router.route(query)
        
        # B for verify
        assert path in ["B", "D"]
    
    @pytest.mark.asyncio
    async def test_router_default_path(self):
        """Router defaults to D for unclear queries."""
        from services.orchestrator.core.router import IntentionRouter
        import os
        
        old_key = os.environ.pop("OPENROUTER_API_KEY", None)
        
        try:
            router = IntentionRouter()
            query = "Something unrelated"
            path = await router.route(query)
            
            # Should default to D
            assert path == "D"
        finally:
            if old_key:
                os.environ["OPENROUTER_API_KEY"] = old_key


class TestConsensusEngine:
    """Tests for consensus engine."""
    
    def test_consensus_init(self):
        """Consensus engine initializes correctly."""
        from services.orchestrator.core.consensus import ConsensusEngine
        
        engine = ConsensusEngine(max_rounds=3)
        
        assert engine.max_rounds == 3
        assert engine.generator is not None
        assert engine.critic is not None
        assert engine.judge is not None
    
    @pytest.mark.asyncio
    async def test_consensus_basic(self):
        """Consensus reaches result."""
        from services.orchestrator.core.consensus import ConsensusEngine
        
        engine = ConsensusEngine(max_rounds=1)
        
        result = await engine.reach_consensus(
            query="Test query",
            facts=[{"text": "Test fact"}],
            sources=[{"url": "example.com"}],
        )
        
        assert "final_answer" in result
        assert "confidence" in result
        assert "rounds" in result


class TestRouterNode:
    """Tests for router node function."""
    
    @pytest.mark.asyncio
    async def test_router_node(self):
        """Router node updates state."""
        from services.orchestrator.core.router import router_node
        
        state = {"query": "Compare X and Y"}
        result = await router_node(state)
        
        assert "path" in result
        assert result["path"] in ["A", "B", "C", "D"]


class TestConsensusNode:
    """Tests for consensus node function."""
    
    @pytest.mark.asyncio
    async def test_consensus_node(self):
        """Consensus node updates state."""
        from services.orchestrator.core.consensus import consensus_node
        
        state = {
            "query": "Test",
            "facts": [{"text": "Fact"}],
            "sources": [],
        }
        result = await consensus_node(state)
        
        assert "generator_output" in result
        assert "confidence" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
