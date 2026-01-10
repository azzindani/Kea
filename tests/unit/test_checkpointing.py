"""
Unit Tests: Checkpointing.

Tests for services/orchestrator/core/checkpointing.py
"""

import pytest


class TestCheckpointStore:
    """Tests for checkpoint store."""
    
    def test_init_memory(self):
        """Initialize in-memory store."""
        from services.orchestrator.core.checkpointing import CheckpointStore
        
        store = CheckpointStore(use_memory=True)
        
        assert store is not None
    
    @pytest.mark.asyncio
    async def test_save_checkpoint(self):
        """Save checkpoint."""
        from services.orchestrator.core.checkpointing import CheckpointStore
        
        store = CheckpointStore(use_memory=True)
        
        state = {
            "job_id": "test-job",
            "query": "Test query",
            "status": "running",
            "iteration": 2,
        }
        
        checkpoint_id = await store.save("test-job", state)
        
        assert checkpoint_id is not None
    
    @pytest.mark.asyncio
    async def test_load_checkpoint(self):
        """Load checkpoint."""
        from services.orchestrator.core.checkpointing import CheckpointStore
        
        store = CheckpointStore(use_memory=True)
        
        state = {"job_id": "load-test", "data": "test"}
        await store.save("load-test", state)
        
        loaded = await store.load("load-test")
        
        assert loaded is not None
        assert loaded["job_id"] == "load-test"
    
    @pytest.mark.asyncio
    async def test_load_nonexistent(self):
        """Load nonexistent checkpoint returns None."""
        from services.orchestrator.core.checkpointing import CheckpointStore
        
        store = CheckpointStore(use_memory=True)
        
        loaded = await store.load("nonexistent")
        
        assert loaded is None
    
    @pytest.mark.asyncio
    async def test_delete_checkpoint(self):
        """Delete checkpoint."""
        from services.orchestrator.core.checkpointing import CheckpointStore
        
        store = CheckpointStore(use_memory=True)
        
        await store.save("del-test", {"data": "value"})
        await store.delete("del-test")
        
        loaded = await store.load("del-test")
        
        assert loaded is None


class TestCheckpointStoreFactory:
    """Tests for factory function."""
    
    def test_get_store(self):
        """Get checkpoint store singleton."""
        from services.orchestrator.core.checkpointing import get_checkpoint_store
        
        store = get_checkpoint_store()
        
        assert store is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
