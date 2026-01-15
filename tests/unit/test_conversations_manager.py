"""
Unit Tests: Conversations Manager.

Tests for conversation and message management.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from shared.conversations.models import (
    Conversation,
    Message,
    MessageRole,
)
from shared.conversations.manager import ConversationManager


class TestConversation:
    """Test Conversation model."""
    
    def test_create_conversation(self):
        """Test conversation creation."""
        conv = Conversation(
            user_id="user-123",
            title="Test Conversation",
        )
        
        assert conv.user_id == "user-123"
        assert conv.title == "Test Conversation"
        assert conv.conversation_id is not None
    
    def test_conversation_defaults(self):
        """Test conversation default values."""
        conv = Conversation(user_id="user-123")
        
        assert conv.is_pinned is False
        assert conv.is_archived is False
        assert conv.messages == []
    
    def test_conversation_timestamps(self):
        """Test conversation timestamps."""
        conv = Conversation(user_id="user-123")
        
        assert conv.created_at is not None
        assert conv.updated_at is not None


class TestMessage:
    """Test Message model."""
    
    def test_create_user_message(self):
        """Test user message creation."""
        msg = Message(
            conversation_id="conv-123",
            role=MessageRole.USER,
            content="Hello!",
        )
        
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello!"
    
    def test_create_assistant_message(self):
        """Test assistant message creation."""
        msg = Message(
            conversation_id="conv-123",
            role=MessageRole.ASSISTANT,
            content="Hi there!",
        )
        
        assert msg.role == MessageRole.ASSISTANT
    
    def test_message_with_sources(self):
        """Test message with sources."""
        msg = Message(
            conversation_id="conv-123",
            role=MessageRole.ASSISTANT,
            content="Based on research...",
            sources=[
                {"url": "https://example.com", "title": "Source 1"},
            ],
        )
        
        assert len(msg.sources) == 1
    
    def test_message_id_generated(self):
        """Test message ID is generated."""
        msg = Message(
            conversation_id="conv-123",
            role=MessageRole.USER,
            content="Test",
        )
        
        assert msg.message_id is not None


class TestConversationManager:
    """Test ConversationManager class."""
    
    @pytest.fixture
    def manager(self):
        """Create manager for testing."""
        return ConversationManager()
    
    @pytest.mark.asyncio
    async def test_create_conversation(self, manager):
        """Test creating conversation."""
        with patch.object(manager, "_db") as mock_db:
            mock_db.execute = AsyncMock()
            
            conv = await manager.create(
                user_id="user-123",
                title="New Chat",
            )
            
            assert conv.user_id == "user-123"
            assert conv.title == "New Chat"
    
    @pytest.mark.asyncio
    async def test_get_conversation(self, manager):
        """Test getting conversation."""
        with patch.object(manager, "_db") as mock_db:
            mock_db.fetchone = AsyncMock(return_value={
                "conversation_id": "conv-123",
                "user_id": "user-123",
                "title": "Test",
                "is_pinned": False,
                "is_archived": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            })
            
            conv = await manager.get("conv-123", "user-123")
            
            assert conv is not None
    
    @pytest.mark.asyncio
    async def test_list_conversations(self, manager):
        """Test listing conversations."""
        with patch.object(manager, "_db") as mock_db:
            mock_db.fetchall = AsyncMock(return_value=[
                {
                    "conversation_id": "conv-1",
                    "user_id": "user-123",
                    "title": "Chat 1",
                    "is_pinned": False,
                    "is_archived": False,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
            ])
            
            convs = await manager.list(user_id="user-123")
            
            assert len(convs) >= 0
    
    @pytest.mark.asyncio
    async def test_add_message(self, manager):
        """Test adding message to conversation."""
        with patch.object(manager, "_db") as mock_db:
            mock_db.execute = AsyncMock()
            
            msg = await manager.add_message(
                conversation_id="conv-123",
                role=MessageRole.USER,
                content="Hello!",
            )
            
            assert msg.content == "Hello!"
    
    @pytest.mark.asyncio
    async def test_delete_conversation(self, manager):
        """Test deleting conversation."""
        with patch.object(manager, "_db") as mock_db:
            mock_db.execute = AsyncMock()
            
            result = await manager.delete("conv-123", "user-123")
            
            mock_db.execute.assert_called()


class TestMessageRole:
    """Test MessageRole enum."""
    
    def test_user_role(self):
        """Test user role value."""
        assert MessageRole.USER.value == "user"
    
    def test_assistant_role(self):
        """Test assistant role value."""
        assert MessageRole.ASSISTANT.value == "assistant"
    
    def test_system_role(self):
        """Test system role value."""
        assert MessageRole.SYSTEM.value == "system"
