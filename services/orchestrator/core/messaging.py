"""
Inter-Agent Messaging System.

Provides communication between agents with:
- Direct messaging
- Broadcast to teams/departments
- Request-response patterns
- Message persistence (optional)
"""

from __future__ import annotations

import asyncio
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Awaitable

from shared.logging import get_logger


logger = get_logger(__name__)


class MessageType(str, Enum):
    """Types of messages."""
    REQUEST = "request"       # Requires response
    RESPONSE = "response"     # Response to request
    INFO = "info"            # Informational
    ALERT = "alert"          # Urgent notification
    BROADCAST = "broadcast"  # To all in scope
    HEARTBEAT = "heartbeat"  # Keep-alive


class MessagePriority(str, Enum):
    """Message priority."""
    URGENT = "urgent"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class Message:
    """
    Agent-to-agent message.
    
    Supports direct, broadcast, and request-response patterns.
    """
    message_id: str
    from_agent: str
    to_agent: str | list[str]  # Direct or list of recipients
    message_type: MessageType
    content: dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    
    # Request-response correlation
    correlation_id: str | None = None  # Links response to request
    reply_to: str | None = None        # Original message ID
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    ttl_seconds: int = 300  # Time to live
    
    @classmethod
    def create(
        cls,
        from_agent: str,
        to_agent: str | list[str],
        message_type: MessageType,
        content: dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        correlation_id: str | None = None,
    ) -> "Message":
        """Create new message."""
        return cls(
            message_id=f"msg_{uuid.uuid4().hex[:12]}",
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            priority=priority,
            correlation_id=correlation_id or f"corr_{uuid.uuid4().hex[:8]}",
        )
    
    def create_response(self, content: dict[str, Any]) -> "Message":
        """Create response to this message."""
        return Message.create(
            from_agent=self.to_agent if isinstance(self.to_agent, str) else "system",
            to_agent=self.from_agent,
            message_type=MessageType.RESPONSE,
            content=content,
            correlation_id=self.correlation_id,
        )


# Type for message handlers
MessageHandler = Callable[[Message], Awaitable[None]]


class MessageBus:
    """
    Async message routing between agents.
    
    Features:
    - Direct messaging
    - Broadcast to groups
    - Request-response with timeout
    - Priority queuing
    
    Example:
        bus = MessageBus()
        
        # Subscribe to messages
        await bus.subscribe("agent_123", handler)
        
        # Send direct message
        await bus.send(Message.create(
            "agent_a", "agent_b",
            MessageType.INFO,
            {"data": "hello"}
        ))
        
        # Request with response
        response = await bus.request(
            "agent_a", "agent_b",
            {"query": "data"},
            timeout=30.0
        )
    """
    
    def __init__(self, max_queue_size: int = 1000):
        self._subscribers: dict[str, MessageHandler] = {}
        self._queues: dict[str, asyncio.Queue] = {}
        self._pending_responses: dict[str, asyncio.Future] = {}
        self._max_queue_size = max_queue_size
        self._message_count = 0
    
    async def subscribe(self, agent_id: str, handler: MessageHandler) -> None:
        """Subscribe agent to receive messages."""
        self._subscribers[agent_id] = handler
        self._queues[agent_id] = asyncio.Queue(maxsize=self._max_queue_size)
        logger.debug(f"Agent {agent_id} subscribed to message bus")
    
    async def unsubscribe(self, agent_id: str) -> None:
        """Unsubscribe agent."""
        self._subscribers.pop(agent_id, None)
        self._queues.pop(agent_id, None)
        logger.debug(f"Agent {agent_id} unsubscribed from message bus")
    
    async def send(self, message: Message) -> bool:
        """
        Send message to recipient(s).
        
        Returns True if delivered to at least one recipient.
        """
        recipients = (
            [message.to_agent] 
            if isinstance(message.to_agent, str) 
            else message.to_agent
        )
        
        delivered = False
        for recipient in recipients:
            if recipient in self._subscribers:
                handler = self._subscribers[recipient]
                try:
                    await handler(message)
                    delivered = True
                    self._message_count += 1
                except Exception as e:
                    logger.error(f"Handler error for {recipient}: {e}")
            elif recipient in self._queues:
                try:
                    self._queues[recipient].put_nowait(message)
                    delivered = True
                    self._message_count += 1
                except asyncio.QueueFull:
                    logger.warning(f"Queue full for {recipient}")
        
        if not delivered:
            logger.warning(f"No recipients for message {message.message_id}")
        
        # Handle response correlation
        if message.message_type == MessageType.RESPONSE:
            if message.correlation_id in self._pending_responses:
                self._pending_responses[message.correlation_id].set_result(message)
        
        return delivered
    
    async def broadcast(
        self,
        from_agent: str,
        content: dict[str, Any],
        scope: str = "all",  # "all", department_id, or team_id
    ) -> int:
        """
        Broadcast message to all agents in scope.
        
        Returns number of recipients.
        """
        recipients = list(self._subscribers.keys())
        
        if scope != "all":
            # Filter by scope (would integrate with Organization)
            # For now, send to all
            pass
        
        message = Message.create(
            from_agent=from_agent,
            to_agent=recipients,
            message_type=MessageType.BROADCAST,
            content=content,
        )
        
        count = 0
        for recipient in recipients:
            if recipient != from_agent:  # Don't send to self
                if await self.send(Message.create(
                    from_agent, recipient, MessageType.BROADCAST, content
                )):
                    count += 1
        
        logger.debug(f"Broadcast to {count} recipients")
        return count
    
    async def request(
        self,
        from_agent: str,
        to_agent: str,
        content: dict[str, Any],
        timeout: float = 30.0,
    ) -> Message | None:
        """
        Send request and wait for response.
        
        Returns response message or None on timeout.
        """
        message = Message.create(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=MessageType.REQUEST,
            content=content,
        )
        
        # Create future for response
        future = asyncio.get_event_loop().create_future()
        self._pending_responses[message.correlation_id] = future
        
        try:
            await self.send(message)
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            logger.warning(f"Request timeout: {message.correlation_id}")
            return None
        finally:
            self._pending_responses.pop(message.correlation_id, None)
    
    async def receive(self, agent_id: str, timeout: float = None) -> Message | None:
        """Receive next message for agent."""
        if agent_id not in self._queues:
            return None
        
        try:
            if timeout:
                message = await asyncio.wait_for(
                    self._queues[agent_id].get(),
                    timeout=timeout
                )
            else:
                message = self._queues[agent_id].get_nowait()
            return message
        except (asyncio.TimeoutError, asyncio.QueueEmpty):
            return None
    
    @property
    def stats(self) -> dict:
        """Bus statistics."""
        return {
            "subscribers": len(self._subscribers),
            "total_messages": self._message_count,
            "pending_responses": len(self._pending_responses),
            "queue_sizes": {
                agent: q.qsize() for agent, q in self._queues.items()
            },
        }


# Global message bus instance
_bus: MessageBus | None = None


def get_message_bus() -> MessageBus:
    """Get or create global message bus."""
    global _bus
    if _bus is None:
        _bus = MessageBus()
    return _bus
