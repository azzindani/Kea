"""
Unit Tests: Checkpointing.

Tests for services/orchestrator/core/checkpointing.py
"""

import pytest


class TestCheckpointStore:
    """Tests for checkpoint store."""
    
    @pytest.mark.asyncio
    async def test_init_memory(self):
        """Initialize checkpoint store with in-memory fallback."""
        from services.orchestrator.core.checkpointing import CheckpointStore
        
        store = CheckpointStore()
        # Don't call initialize() - it requires database
        # Store should work without initialization (memory fallback)
        
        assert store is not None
    
    @pytest.mark.asyncio
    async def test_save_checkpoint(self):
        """Save checkpoint to store."""
        from services.orchestrator.core.checkpointing import CheckpointStore
        
        store = CheckpointStore()
        # Use in-memory by not initializing database
        
        state = {"job_id": "test-job", "query": "test", "status": "running"}
        
        await store.save("test-job", "router", state)
        
        # Verify save worked by loading
        loaded = await store.load("test-job", "router")
        assert loaded == state
    
    @pytest.mark.asyncio
    async def test_load_checkpoint(self):
        """Load checkpoint from store."""
        from services.orchestrator.core.checkpointing import CheckpointStore
        
        store = CheckpointStore()
        
        state = {"iteration": 1, "facts": []}
        await store.save("load-job", "planner", state)
        
        loaded = await store.load("load-job", "planner")
        
        assert loaded is not None
        assert loaded["iteration"] == 1
    
    @pytest.mark.asyncio
    async def test_load_nonexistent(self):
        """Load non-existent checkpoint returns None."""
        from services.orchestrator.core.checkpointing import CheckpointStore
        
        store = CheckpointStore()
        
        loaded = await store.load("nonexistent-job", "nonexistent-node")
        
        assert loaded is None
    
    @pytest.mark.asyncio
    async def test_delete_checkpoint(self):
        """Delete job checkpoints."""
        from services.orchestrator.core.checkpointing import CheckpointStore
        
        store = CheckpointStore()
        
        await store.save("del-job", "node1", {"data": "test"})
        
        count = await store.delete_job_checkpoints("del-job")
        
        assert count >= 1
        
        # Verify deleted
        loaded = await store.load("del-job", "node1")
        assert loaded is None


class TestCheckpointStoreFactory:
    """Tests for checkpoint store factory."""
    
    @pytest.mark.asyncio
    async def test_get_store(self):
        """Get global checkpoint store."""
        from services.orchestrator.core.checkpointing import get_checkpoint_store
        
        store = await get_checkpoint_store()
        
        assert store is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
