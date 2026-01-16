"""
Tests for ConsensusEngine.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestConsensusEngine:
    """Tests for ConsensusEngine."""
    
    def test_import_consensus(self):
        """Test that consensus can be imported."""
        from services.orchestrator.core.consensus import (
            ConsensusEngine,
            consensus_node,
        )
        assert ConsensusEngine is not None
        assert consensus_node is not None
    
    def test_create_consensus_engine(self):
        """Test creating consensus engine."""
        from services.orchestrator.core.consensus import ConsensusEngine
        
        engine = ConsensusEngine(max_rounds=3)
        assert engine.max_rounds == 3
        assert engine.generator is not None
        assert engine.critic is not None
        assert engine.judge is not None
    
    def test_default_max_rounds(self):
        """Test default max rounds."""
        from services.orchestrator.core.consensus import ConsensusEngine
        
        engine = ConsensusEngine()
        assert engine.max_rounds == 2
    
    @pytest.mark.asyncio
    async def test_reach_consensus(self):
        """Test reaching consensus."""
        from services.orchestrator.core.consensus import ConsensusEngine
        
        with patch.dict('os.environ', {}, clear=True):
            engine = ConsensusEngine(max_rounds=1)
            
            result = await engine.reach_consensus(
                query="What is AI?",
                facts=["AI is artificial intelligence"],
                sources=["wiki"],
            )
            
            assert "final_answer" in result
            assert "confidence" in result
            assert "rounds" in result
            assert "history" in result


class TestConsensusNode:
    """Tests for consensus_node function."""
    
    def test_import_consensus_node(self):
        """Test consensus_node can be imported."""
        from services.orchestrator.core.consensus import consensus_node
        assert consensus_node is not None
    
    @pytest.mark.asyncio
    async def test_consensus_node_updates_state(self):
        """Test consensus_node updates state correctly."""
        from services.orchestrator.core.consensus import consensus_node
        
        with patch.dict('os.environ', {}, clear=True):
            state = {
                "query": "Test query",
                "facts": ["Fact 1"],
                "sources": ["Source 1"],
            }
            
            result = await consensus_node(state)
            
            assert "generator_output" in result
            assert "confidence" in result
            assert "consensus_rounds" in result
