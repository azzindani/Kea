"""
Tests for conversations manager.
"""


import pytest


class TestConversation:
    """Tests for Conversation model."""

    def test_import_conversation(self):
        """Test that Conversation can be imported."""
        from shared.conversations.manager import Conversation
        assert Conversation is not None

    def test_create_conversation(self):
        """Test creating conversation."""
        from shared.conversations.manager import Conversation

        conv = Conversation(
            conversation_id="conv_123",
            user_id="user_456",
            title="Test Conversation",
        )

        assert conv.conversation_id == "conv_123"
        assert conv.user_id == "user_456"
        assert conv.title == "Test Conversation"

    def test_conversation_has_message_count(self):
        """Test conversation has message_count attribute."""
        from shared.conversations.manager import Conversation

        conv = Conversation(
            conversation_id="conv_1",
            user_id="user_1",
        )

        assert hasattr(conv, "message_count")


class TestMessage:
    """Tests for Message model."""

    def test_import_message(self):
        """Test that Message can be imported."""
        from shared.conversations.manager import Message
        assert Message is not None

    def test_create_message(self):
        """Test creating message with all required fields."""
        from shared.conversations.manager import Message

        msg = Message(
            message_id="msg_123",
            conversation_id="conv_456",
            role="user",
            content="Hello",
        )

        assert msg.message_id == "msg_123"
        assert msg.conversation_id == "conv_456"
        assert msg.role == "user"
        assert msg.content == "Hello"


class TestConversationManager:
    """Tests for ConversationManager."""

    def test_import_manager(self):
        """Test that ConversationManager can be imported."""
        from shared.conversations.manager import (
            ConversationManager,
            get_conversation_manager,
        )
        assert ConversationManager is not None
        assert get_conversation_manager is not None

    def test_create_manager(self):
        """Test creating conversation manager."""
        from shared.conversations.manager import ConversationManager

        manager = ConversationManager()
        assert manager is not None

    @pytest.mark.asyncio
    async def test_manager_initialize(self):
        """Test manager initialization."""
        from shared.conversations.manager import ConversationManager

        manager = ConversationManager()
        await manager.initialize()
        # Should not raise

    @pytest.mark.asyncio
    async def test_create_conversation(self):
        """Test creating conversation via manager."""
        from shared.conversations.manager import ConversationManager

        manager = ConversationManager()
        await manager.initialize()

        conv = await manager.create_conversation(
            user_id="user_123",
            title="Test",
        )

        assert conv.user_id == "user_123"

    @pytest.mark.asyncio
    async def test_get_conversation(self):
        """Test getting conversation."""
        from shared.conversations.manager import ConversationManager

        manager = ConversationManager()
        await manager.initialize()

        # Create first
        conv = await manager.create_conversation(
            user_id="user_1",
            title="Test",
        )

        # Then get
        retrieved = await manager.get_conversation(conv.conversation_id)
        assert retrieved is not None
        assert retrieved.user_id == "user_1"
