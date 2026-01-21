"""
Queue Abstraction.

Provides unified interface for Redis and in-memory queues.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from shared.logging import get_logger


logger = get_logger(__name__)


@dataclass
class QueueMessage:
    """Message in queue."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    data: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    attempts: int = 0


class Queue(ABC):
    """Abstract queue interface."""
    
    @abstractmethod
    async def push(self, data: dict) -> str:
        """Push message to queue. Returns message ID."""
        pass
    
    @abstractmethod
    async def pop(self, timeout: float = 0) -> QueueMessage | None:
        """Pop message from queue."""
        pass
    
    @abstractmethod
    async def ack(self, message_id: str) -> None:
        """Acknowledge message (mark as processed)."""
        pass
    
    @abstractmethod
    async def nack(self, message_id: str) -> None:
        """Negative acknowledge (requeue for retry)."""
        pass
    
    @abstractmethod
    async def size(self) -> int:
        """Get queue size."""
        pass


class InMemoryQueue(Queue):
    """In-memory queue for development/testing."""
    
    def __init__(self, name: str = "default") -> None:
        self.name = name
        self._queue: asyncio.Queue[QueueMessage] = asyncio.Queue()
        self._processing: dict[str, QueueMessage] = {}
    
    async def push(self, data: dict) -> str:
        """Push message to queue."""
        msg = QueueMessage(data=data)
        await self._queue.put(msg)
        logger.debug(f"Pushed message {msg.id} to {self.name}")
        return msg.id
    
    async def pop(self, timeout: float = 0) -> QueueMessage | None:
        """Pop message from queue."""
        try:
            if timeout > 0:
                msg = await asyncio.wait_for(self._queue.get(), timeout=timeout)
            else:
                msg = self._queue.get_nowait()
            
            msg.attempts += 1
            self._processing[msg.id] = msg
            return msg
            
        except (asyncio.TimeoutError, asyncio.QueueEmpty):
            return None
    
    async def ack(self, message_id: str) -> None:
        """Acknowledge message."""
        self._processing.pop(message_id, None)
    
    async def nack(self, message_id: str) -> None:
        """Requeue message."""
        msg = self._processing.pop(message_id, None)
        if msg:
            await self._queue.put(msg)
    
    async def size(self) -> int:
        """Get queue size."""
        return self._queue.qsize()


class RedisQueue(Queue):
    """Redis-backed queue for production."""
    
    def __init__(
        self,
        name: str = "research_jobs",
        redis_url: str | None = None,
    ) -> None:
        self.name = name
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._redis = None
    
    async def _get_redis(self):
        """Get or create Redis connection."""
        if self._redis is None:
            import redis.asyncio as redis
            self._redis = redis.from_url(self.redis_url)
        return self._redis
    
    async def push(self, data: dict) -> str:
        """Push message to Redis list."""
        import json
        
        redis = await self._get_redis()
        msg = QueueMessage(data=data)
        
        await redis.lpush(self.name, json.dumps({
            "id": msg.id,
            "data": msg.data,
            "created_at": msg.created_at.isoformat(),
            "attempts": msg.attempts,
        }))
        
        return msg.id
    
    async def pop(self, timeout: float = 0) -> QueueMessage | None:
        """Pop message from Redis list."""
        import json
        
        redis = await self._get_redis()
        
        if timeout > 0:
            result = await redis.brpop(self.name, timeout=int(timeout))
        else:
            result = await redis.rpop(self.name)
        
        if not result:
            return None
        
        # brpop returns (key, value), rpop returns just value
        data_str = result[1] if isinstance(result, tuple) else result
        data = json.loads(data_str)
        
        return QueueMessage(
            id=data["id"],
            data=data["data"],
            created_at=datetime.fromisoformat(data["created_at"]),
            attempts=data["attempts"] + 1,
        )
    
    async def ack(self, message_id: str) -> None:
        """Acknowledge (no-op for simple Redis queue)."""
        pass
    
    async def nack(self, message_id: str) -> None:
        """Requeue not implemented for simple Redis queue."""
        pass
    
    async def size(self) -> int:
        """Get queue size."""
        redis = await self._get_redis()
        return await redis.llen(self.name)


def create_queue(name: str = "research_jobs", use_memory: bool = False) -> Queue:
    """Create queue based on configuration."""
    if use_memory or not os.getenv("DATABASE_URL"):
        return InMemoryQueue(name)
    
    from shared.queue.postgres_queue import PostgresQueue
    return PostgresQueue(name)
