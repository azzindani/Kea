"""
Unit Tests: Workers.

Tests for workers/*.py
"""

import pytest


class TestResearchWorker:
    """Tests for research worker."""
    
    def test_worker_init(self):
        """Worker initializes."""
        from workers.research_worker import ResearchWorker
        
        worker = ResearchWorker()
        assert worker is not None
    
    @pytest.mark.asyncio
    async def test_process_job(self):
        """Worker can process job."""
        from workers.research_worker import ResearchWorker
        
        worker = ResearchWorker()
        job = {"id": "test-001", "query": "Test query", "depth": 1}
        
        result = await worker.process_job(job)
        
        assert "status" in result


class TestSynthesisWorker:
    """Tests for synthesis worker."""
    
    def test_worker_init(self):
        """Worker initializes."""
        from workers.synthesis_worker import SynthesisWorker
        
        worker = SynthesisWorker()
        assert worker is not None
    
    @pytest.mark.asyncio
    async def test_process_job(self):
        """Worker can process job."""
        from workers.synthesis_worker import SynthesisWorker
        
        worker = SynthesisWorker()
        job = {"id": "synth-001", "topic": "Test", "sources": []}
        
        result = await worker.process_job(job)
        
        assert "status" in result


class TestShadowLabWorker:
    """Tests for shadow lab worker."""
    
    def test_worker_init(self):
        """Worker initializes."""
        from workers.shadow_lab_worker import ShadowLabWorker
        
        worker = ShadowLabWorker()
        assert worker is not None
    
    @pytest.mark.asyncio
    async def test_process_job(self):
        """Worker can process job."""
        from workers.shadow_lab_worker import ShadowLabWorker
        
        worker = ShadowLabWorker()
        job = {"id": "verify-001", "claim": "Test claim", "original_sources": []}
        
        result = await worker.process_job(job)
        
        assert "status" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
