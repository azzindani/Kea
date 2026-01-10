"""
Unit Tests: Workers.

Tests for workers/*.py
"""

import pytest


class TestResearchWorker:
    """Tests for research worker."""
    
    def test_init(self):
        """Initialize worker."""
        from workers.research_worker import ResearchWorker
        
        worker = ResearchWorker()
        
        assert worker is not None
        assert worker._running is False


class TestSynthesisWorker:
    """Tests for synthesis worker."""
    
    def test_init(self):
        """Initialize worker."""
        from workers.synthesis_worker import SynthesisWorker
        
        worker = SynthesisWorker()
        
        assert worker is not None
        assert worker._running is False


class TestShadowLabWorker:
    """Tests for shadow lab worker."""
    
    def test_init(self):
        """Initialize worker."""
        from workers.shadow_lab_worker import ShadowLabWorker
        
        worker = ShadowLabWorker()
        
        assert worker is not None
        assert worker._running is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
