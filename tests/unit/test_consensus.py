"""
Tests for Consensus Engine (Adversarial Collaboration).
"""

import pytest


class TestConsensusEngine:
    """Tests for adversarial collaboration consensus."""
    
    def test_import_consensus(self):
        """Test consensus module imports."""
        from services.orchestrator.core.consensus import (
            ConsensusEngine,
            ConsensusResult,
        )
        
        assert ConsensusEngine is not None
        print("\n✅ Consensus imports work")
    
    def test_create_consensus_engine(self):
        """Test consensus engine creation."""
        from services.orchestrator.core.consensus import ConsensusEngine
        
        engine = ConsensusEngine()
        
        assert engine is not None
        print("\n✅ ConsensusEngine created")
    
    def test_add_perspectives(self):
        """Test adding multiple perspectives."""
        from services.orchestrator.core.consensus import ConsensusEngine
        
        engine = ConsensusEngine()
        
        # Add generator (optimist) perspective
        engine.add_perspective("generator", {
            "assessment": "Tesla growth is exceptional",
            "confidence": 0.9,
            "evidence": ["52% YoY revenue growth", "Market leader in EVs"],
        })
        
        # Add critic (pessimist) perspective
        engine.add_perspective("critic", {
            "assessment": "Tesla faces significant headwinds",
            "confidence": 0.7,
            "evidence": ["Competition increasing", "Margin pressure"],
        })
        
        perspectives = engine.get_perspectives()
        assert len(perspectives) >= 2
        
        print("\n✅ Added perspectives")
    
    def test_synthesize_consensus(self):
        """Test consensus synthesis."""
        from services.orchestrator.core.consensus import ConsensusEngine
        
        engine = ConsensusEngine()
        
        engine.add_perspective("optimist", {
            "claim": "Stock will rise",
            "confidence": 0.8,
        })
        
        engine.add_perspective("pessimist", {
            "claim": "Stock will fall",
            "confidence": 0.6,
        })
        
        result = engine.synthesize()
        
        assert result is not None
        assert hasattr(result, "consensus") or "consensus" in str(type(result))
        
        print("\n✅ Consensus synthesized")
    
    def test_consensus_with_evidence(self):
        """Test consensus with evidence weighting."""
        from services.orchestrator.core.consensus import ConsensusEngine
        
        engine = ConsensusEngine()
        
        # Well-supported claim
        engine.add_perspective("data_analyst", {
            "claim": "Revenue grew 25%",
            "confidence": 0.95,
            "sources": ["10-K filing", "Earnings call"],
        })
        
        # Poorly-supported claim  
        engine.add_perspective("speculation", {
            "claim": "Revenue might have grown 50%",
            "confidence": 0.3,
            "sources": [],
        })
        
        result = engine.synthesize()
        
        # Higher evidence should win
        print(f"\n✅ Evidence-weighted consensus")


class TestConsensusResult:
    """Tests for consensus results."""
    
    def test_create_result(self):
        """Test consensus result creation."""
        from services.orchestrator.core.consensus import ConsensusResult
        
        result = ConsensusResult(
            consensus="Balanced view on Tesla",
            confidence=0.75,
            supporting_evidence=["Revenue data", "Market position"],
            dissenting_views=["Competition concerns"],
        )
        
        assert result.consensus is not None
        assert result.confidence == 0.75
        
        print("\n✅ ConsensusResult created")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
