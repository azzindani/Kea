"""
Unit Tests: Queue.

Tests for shared/queue/queue.py.
"""

import pytest


class TestInMemoryQueue:
    """Tests for in-memory queue."""
    
    @pytest.mark.asyncio
    async def test_push_pop(self):
        """Push and pop message."""
        from shared.queue import InMemoryQueue
        
        queue = InMemoryQueue("test")
        
        msg_id = await queue.push({"data": "test"})
        assert msg_id is not None
        
        msg = await queue.pop(timeout=1)
        assert msg is not None
        assert msg.data["data"] == "test"
    
    @pytest.mark.asyncio
    async def test_queue_size(self):
        """Queue size tracking."""
        from shared.queue import InMemoryQueue
        
        queue = InMemoryQueue("size-test")
        
        assert await queue.size() == 0
        
        await queue.push({"a": 1})
        await queue.push({"b": 2})
        
        assert await queue.size() == 2
    
    @pytest.mark.asyncio
    async def test_empty_pop_returns_none(self):
        """Pop from empty queue returns None."""
        from shared.queue import InMemoryQueue
        
        queue = InMemoryQueue("empty")
        
        msg = await queue.pop(timeout=0)
        assert msg is None
    
    @pytest.mark.asyncio
    async def test_ack_message(self):
        """Acknowledge message."""
        from shared.queue import InMemoryQueue
        
        queue = InMemoryQueue("ack-test")
        
        await queue.push({"test": True})
        msg = await queue.pop(timeout=1)
        
        # Should not raise
        await queue.ack(msg.id)


class TestQueueFactory:
    """Tests for queue factory."""
    
    def test_create_memory_queue(self):
        """Create in-memory queue."""
        from shared.queue import create_queue
        
        queue = create_queue("test-queue", use_memory=True)
        
        assert queue is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
