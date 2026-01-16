"""
Integration Tests: Conversation API.

Tests for ChatGPT-style conversation management.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from services.api_gateway.main import app


@pytest.fixture
def test_user():
    """Test user data."""
    return {
        "email": "conv_test@example.com",
        "name": "Conversation Tester",
        "password": "SecurePassword123!",
    }


@pytest.fixture
async def async_client():
    """Create async HTTP client with proper app lifecycle."""
    from asgi_lifespan import LifespanManager
    
    async with LifespanManager(app) as manager:
        transport = ASGITransport(app=manager.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


@pytest.fixture
async def auth_headers(async_client, test_user):
    """Get auth headers for authenticated requests."""
    response = await async_client.post(
        "/api/v1/auth/register",
        json=test_user,
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestConversationCRUD:
    """Test conversation CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_create_conversation(self, async_client, auth_headers):
        """Test creating a new conversation."""
        response = await async_client.post(
            "/api/v1/conversations",
            headers=auth_headers,
            json={"title": "Test Conversation"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "conversation_id" in data
        assert data["title"] == "Test Conversation"
        assert data["message_count"] == 0
        assert data["is_archived"] is False
    
    @pytest.mark.asyncio
    async def test_list_conversations(self, async_client, auth_headers):
        """Test listing conversations."""
        # Create some conversations
        for i in range(3):
            await async_client.post(
                "/api/v1/conversations",
                headers=auth_headers,
                json={"title": f"Conv {i}"},
            )
        
        # List
        response = await async_client.get(
            "/api/v1/conversations",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] >= 3
        assert len(data["conversations"]) >= 3
    
    @pytest.mark.asyncio
    async def test_get_conversation(self, async_client, auth_headers):
        """Test getting a single conversation."""
        # Create
        create_response = await async_client.post(
            "/api/v1/conversations",
            headers=auth_headers,
            json={"title": "Get Test"},
        )
        conv_id = create_response.json()["conversation_id"]
        
        # Get
        response = await async_client.get(
            f"/api/v1/conversations/{conv_id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["conversation"]["conversation_id"] == conv_id
        assert "messages" in data
    
    @pytest.mark.asyncio
    async def test_update_conversation(self, async_client, auth_headers):
        """Test updating conversation."""
        # Create
        create_response = await async_client.post(
            "/api/v1/conversations",
            headers=auth_headers,
            json={"title": "Original"},
        )
        conv_id = create_response.json()["conversation_id"]
        
        # Update
        response = await async_client.put(
            f"/api/v1/conversations/{conv_id}",
            headers=auth_headers,
            json={"title": "Updated", "is_pinned": True},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == "Updated"
        assert data["is_pinned"] is True
    
    @pytest.mark.asyncio
    async def test_archive_conversation(self, async_client, auth_headers):
        """Test archiving conversation."""
        # Create
        create_response = await async_client.post(
            "/api/v1/conversations",
            headers=auth_headers,
            json={"title": "To Archive"},
        )
        conv_id = create_response.json()["conversation_id"]
        
        # Archive
        response = await async_client.put(
            f"/api/v1/conversations/{conv_id}",
            headers=auth_headers,
            json={"is_archived": True},
        )
        
        assert response.status_code == 200
        assert response.json()["is_archived"] is True
        
        # Should not appear in default list
        list_response = await async_client.get(
            "/api/v1/conversations",
            headers=auth_headers,
        )
        conv_ids = [c["conversation_id"] for c in list_response.json()["conversations"]]
        assert conv_id not in conv_ids
        
        # Should appear with include_archived
        list_response = await async_client.get(
            "/api/v1/conversations?include_archived=true",
            headers=auth_headers,
        )
        conv_ids = [c["conversation_id"] for c in list_response.json()["conversations"]]
        assert conv_id in conv_ids
    
    @pytest.mark.asyncio
    async def test_delete_conversation(self, async_client, auth_headers):
        """Test deleting conversation."""
        # Create
        create_response = await async_client.post(
            "/api/v1/conversations",
            headers=auth_headers,
            json={"title": "To Delete"},
        )
        conv_id = create_response.json()["conversation_id"]
        
        # Delete
        response = await async_client.delete(
            f"/api/v1/conversations/{conv_id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        
        # Should not exist
        get_response = await async_client.get(
            f"/api/v1/conversations/{conv_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404


class TestConversationMessages:
    """Test message operations."""
    
    @pytest.mark.asyncio
    async def test_send_message(self, async_client, auth_headers):
        """Test sending a message."""
        # Create conversation
        create_response = await async_client.post(
            "/api/v1/conversations",
            headers=auth_headers,
            json={"title": "Message Test"},
        )
        conv_id = create_response.json()["conversation_id"]
        
        # Send message
        response = await async_client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            headers=auth_headers,
            json={"content": "Hello, how are you?"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "user_message" in data
        assert "assistant_message" in data
        assert data["user_message"]["role"] == "user"
        assert data["assistant_message"]["role"] == "assistant"
    
    @pytest.mark.asyncio
    async def test_auto_title_first_message(self, async_client, auth_headers):
        """Test auto-title from first message."""
        # Create without title
        create_response = await async_client.post(
            "/api/v1/conversations",
            headers=auth_headers,
            json={},
        )
        conv_id = create_response.json()["conversation_id"]
        
        # Send message
        await async_client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            headers=auth_headers,
            json={"content": "What is machine learning?"},
        )
        
        # Check title updated
        get_response = await async_client.get(
            f"/api/v1/conversations/{conv_id}",
            headers=auth_headers,
        )
        title = get_response.json()["conversation"]["title"]
        
        assert "machine learning" in title.lower()
    
    @pytest.mark.asyncio
    async def test_get_messages(self, async_client, auth_headers):
        """Test getting messages."""
        # Create and send messages
        create_response = await async_client.post(
            "/api/v1/conversations",
            headers=auth_headers,
            json={"title": "History Test"},
        )
        conv_id = create_response.json()["conversation_id"]
        
        await async_client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            headers=auth_headers,
            json={"content": "Message 1"},
        )
        await async_client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            headers=auth_headers,
            json={"content": "Message 2"},
        )
        
        # Get messages
        response = await async_client.get(
            f"/api/v1/conversations/{conv_id}/messages",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 2 user + 2 assistant = 4 messages
        assert len(data["messages"]) >= 4


class TestConversationSearch:
    """Test search functionality."""
    
    @pytest.mark.asyncio
    async def test_search_conversations(self, async_client, auth_headers):
        """Test searching conversations."""
        # Create with specific title
        await async_client.post(
            "/api/v1/conversations",
            headers=auth_headers,
            json={"title": "Quantum Computing Research"},
        )
        await async_client.post(
            "/api/v1/conversations",
            headers=auth_headers,
            json={"title": "Classical Music History"},
        )
        
        # Search
        response = await async_client.get(
            "/api/v1/conversations/search?q=quantum",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] >= 1
        assert any("quantum" in c["title"].lower() for c in data["results"])


class TestConversationIsolation:
    """Test user isolation."""
    
    @pytest.mark.asyncio
    async def test_cannot_access_other_users_conversation(self, async_client):
        """Test that users cannot access each other's conversations."""
        # User 1 creates conversation
        user1_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "user1@example.com",
                "name": "User 1",
                "password": "SecurePassword123!",
            },
        )
        user1_token = user1_response.json()["access_token"]
        
        create_response = await async_client.post(
            "/api/v1/conversations",
            headers={"Authorization": f"Bearer {user1_token}"},
            json={"title": "User 1's Private Chat"},
        )
        conv_id = create_response.json()["conversation_id"]
        
        # User 2 tries to access
        user2_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "user2@example.com",
                "name": "User 2",
                "password": "SecurePassword123!",
            },
        )
        user2_token = user2_response.json()["access_token"]
        
        access_response = await async_client.get(
            f"/api/v1/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        
        assert access_response.status_code == 403
