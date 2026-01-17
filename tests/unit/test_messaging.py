"""
Tests for Inter-Agent Messaging System.
"""

import pytest
import asyncio


class TestMessage:
    """Tests for Message model."""
    
    def test_create_message(self):
        """Test message creation."""
        from services.orchestrator.core.messaging import (
            Message, MessageType, MessagePriority
        )
        
        msg = Message.create(
            from_agent="agent_a",
            to_agent="agent_b",
            message_type=MessageType.REQUEST,
            content={"query": "What is the revenue?"},
            priority=MessagePriority.URGENT,
        )
        
        assert msg.message_id.startswith("msg_")
        assert msg.from_agent == "agent_a"
        assert msg.to_agent == "agent_b"
        assert msg.message_type == MessageType.REQUEST
        assert msg.priority == MessagePriority.URGENT
        assert msg.correlation_id is not None
        
        print(f"\n✅ Created message: {msg.message_id}")
    
    def test_create_response(self):
        """Test response creation."""
        from services.orchestrator.core.messaging import Message, MessageType
        
        request = Message.create(
            from_agent="agent_a",
            to_agent="agent_b",
            message_type=MessageType.REQUEST,
            content={"query": "data?"},
        )
        
        response = request.create_response({"answer": "here"})
        
        assert response.message_type == MessageType.RESPONSE
        assert response.correlation_id == request.correlation_id
        assert response.to_agent == "agent_a"  # Response goes back
        assert response.content == {"answer": "here"}
        
        print("\n✅ Response creation works")
    
    def test_broadcast_message(self):
        """Test broadcast to multiple recipients."""
        from services.orchestrator.core.messaging import Message, MessageType
        
        msg = Message.create(
            from_agent="supervisor",
            to_agent=["agent_1", "agent_2", "agent_3"],
            message_type=MessageType.BROADCAST,
            content={"announcement": "All hands meeting"},
        )
        
        assert isinstance(msg.to_agent, list)
        assert len(msg.to_agent) == 3
        
        print("\n✅ Broadcast message created")


class TestMessageBus:
    """Tests for MessageBus."""
    
    @pytest.mark.asyncio
    async def test_subscribe_and_send(self):
        """Test message subscription and sending."""
        from services.orchestrator.core.messaging import (
            MessageBus, Message, MessageType
        )
        
        bus = MessageBus()
        received = []
        
        async def handler(msg):
            received.append(msg)
        
        await bus.subscribe("agent_receiver", handler)
        
        msg = Message.create(
            "agent_sender", "agent_receiver",
            MessageType.INFO, {"data": "hello"}
        )
        
        success = await bus.send(msg)
        
        assert success is True
        assert len(received) == 1
        assert received[0].content == {"data": "hello"}
        
        print("\n✅ Subscribe and send works")
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        """Test unsubscribe."""
        from services.orchestrator.core.messaging import MessageBus, Message, MessageType
        
        bus = MessageBus()
        received = []
        
        async def handler(msg):
            received.append(msg)
        
        await bus.subscribe("agent_temp", handler)
        await bus.unsubscribe("agent_temp")
        
        msg = Message.create("sender", "agent_temp", MessageType.INFO, {})
        success = await bus.send(msg)
        
        assert success is False  # No subscriber
        assert len(received) == 0
        
        print("\n✅ Unsubscribe works")
    
    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test broadcast to all agents."""
        from services.orchestrator.core.messaging import MessageBus
        
        bus = MessageBus()
        received = {"a": [], "b": [], "c": []}
        
        async def make_handler(name):
            async def handler(msg):
                received[name].append(msg)
            return handler
        
        await bus.subscribe("a", await make_handler("a"))
        await bus.subscribe("b", await make_handler("b"))
        await bus.subscribe("c", await make_handler("c"))
        
        count = await bus.broadcast("supervisor", {"alert": "test"})
        
        # Supervisor doesn't receive own broadcast
        assert count >= 2
        
        print(f"\n✅ Broadcast to {count} recipients")
    
    @pytest.mark.asyncio
    async def test_request_response(self):
        """Test request-response pattern."""
        from services.orchestrator.core.messaging import (
            MessageBus, Message, MessageType
        )
        
        bus = MessageBus()
        
        # Responder auto-replies
        async def responder(msg):
            if msg.message_type == MessageType.REQUEST:
                response = msg.create_response({"answer": "42"})
                await bus.send(response)
        
        await bus.subscribe("responder", responder)
        await bus.subscribe("requester", lambda m: None)  # Just to exist
        
        # Send request and wait for response
        response = await bus.request(
            "requester", "responder",
            {"question": "meaning of life?"},
            timeout=5.0
        )
        
        assert response is not None
        assert response.content == {"answer": "42"}
        
        print("\n✅ Request-response pattern works")
    
    @pytest.mark.asyncio
    async def test_request_timeout(self):
        """Test request timeout."""
        from services.orchestrator.core.messaging import MessageBus
        
        bus = MessageBus()
        
        # Subscribe but never respond
        await bus.subscribe("silent", lambda m: None)
        await bus.subscribe("requester", lambda m: None)
        
        response = await bus.request(
            "requester", "silent",
            {"query": "hello?"},
            timeout=0.1  # Very short timeout
        )
        
        assert response is None  # Timed out
        
        print("\n✅ Request timeout works")
    
    def test_bus_stats(self):
        """Test bus statistics."""
        from services.orchestrator.core.messaging import MessageBus
        
        bus = MessageBus()
        stats = bus.stats
        
        assert "subscribers" in stats
        assert "total_messages" in stats
        assert stats["subscribers"] == 0
        
        print(f"\n✅ Bus stats: {stats}")
    
    def test_singleton(self):
        """Test message bus singleton."""
        from services.orchestrator.core.messaging import get_message_bus
        
        bus1 = get_message_bus()
        bus2 = get_message_bus()
        
        assert bus1 is bus2
        
        print("\n✅ MessageBus singleton works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
