"""
End-to-End Tests: Complete User Flow.

Real tests that exercise the full API from registration to research.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from services.api_gateway.main import app


@pytest.fixture
async def async_client():
    """Create async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestCompleteUserFlow:
    """Test complete user journey from signup to research."""
    
    @pytest.mark.asyncio
    async def test_full_user_journey(self, async_client):
        """
        Complete user journey:
        1. Register
        2. Login
        3. Create conversation
        4. Send message
        5. Get history
        6. Logout
        """
        # 1. Register
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "journey@example.com",
                "name": "Journey User",
                "password": "SecurePassword123!",
            },
        )
        assert register_response.status_code == 200
        access_token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 2. Create conversation
        conv_response = await async_client.post(
            "/api/v1/conversations",
            headers=headers,
            json={"title": "My Research"},
        )
        assert conv_response.status_code == 200
        conv_id = conv_response.json()["conversation_id"]
        
        # 3. Send message
        msg_response = await async_client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            headers=headers,
            json={"content": "What is artificial intelligence?"},
        )
        assert msg_response.status_code == 200
        assert "assistant_message" in msg_response.json()
        
        # 4. Get conversation with history
        history_response = await async_client.get(
            f"/api/v1/conversations/{conv_id}",
            headers=headers,
        )
        assert history_response.status_code == 200
        messages = history_response.json()["messages"]
        assert len(messages) >= 2  # At least user + assistant
        
        # 5. List conversations
        list_response = await async_client.get(
            "/api/v1/conversations",
            headers=headers,
        )
        assert list_response.status_code == 200
        assert list_response.json()["total"] >= 1
        
        # 6. Logout
        logout_response = await async_client.post(
            "/api/v1/auth/logout",
            headers=headers,
        )
        assert logout_response.status_code == 200


class TestAPIKeyFlow:
    """Test API key authentication flow."""
    
    @pytest.mark.asyncio
    async def test_api_key_full_flow(self, async_client):
        """
        API key flow:
        1. Register via username/password
        2. Create API key
        3. Use API key for conversation
        4. Revoke API key
        """
        # 1. Register
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "apikey@example.com",
                "name": "API Key User",
                "password": "SecurePassword123!",
            },
        )
        access_token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 2. Create API key
        key_response = await async_client.post(
            "/api/v1/users/me/keys",
            headers=headers,
            json={"name": "E2E Test Key"},
        )
        assert key_response.status_code == 200
        api_key = key_response.json()["raw_key"]
        key_id = key_response.json()["key_id"]
        
        # 3. Use API key for requests
        api_headers = {"X-API-Key": api_key}
        
        conv_response = await async_client.post(
            "/api/v1/conversations",
            headers=api_headers,
            json={"title": "API Key Conversation"},
        )
        assert conv_response.status_code == 200
        
        # 4. Verify key appears in list
        list_response = await async_client.get(
            "/api/v1/users/me/keys",
            headers=headers,
        )
        assert list_response.status_code == 200
        key_names = [k["name"] for k in list_response.json()["keys"]]
        assert "E2E Test Key" in key_names
        
        # 5. Revoke key
        delete_response = await async_client.delete(
            f"/api/v1/users/me/keys/{key_id}",
            headers=headers,
        )
        assert delete_response.status_code == 200
        
        # 6. Verify key no longer works
        blocked_response = await async_client.post(
            "/api/v1/conversations",
            headers=api_headers,
            json={"title": "Should Fail"},
        )
        assert blocked_response.status_code == 401


class TestConversationFlow:
    """Test complete conversation management flow."""
    
    @pytest.fixture
    async def authenticated_client(self, async_client):
        """Create authenticated client."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": f"conv_flow_{id(self)}@example.com",
                "name": "Conv User",
                "password": "SecurePassword123!",
            },
        )
        token = response.json()["access_token"]
        return async_client, {"Authorization": f"Bearer {token}"}
    
    @pytest.mark.asyncio
    async def test_conversation_lifecycle(self, authenticated_client):
        """
        Conversation lifecycle:
        1. Create
        2. Send multiple messages
        3. Pin
        4. Archive
        5. Search
        6. Delete
        """
        client, headers = authenticated_client
        
        # 1. Create
        create_response = await client.post(
            "/api/v1/conversations",
            headers=headers,
            json={"title": "Lifecycle Test"},
        )
        conv_id = create_response.json()["conversation_id"]
        
        # 2. Send multiple messages
        for msg in ["First question", "Follow up", "Another question"]:
            await client.post(
                f"/api/v1/conversations/{conv_id}/messages",
                headers=headers,
                json={"content": msg},
            )
        
        # Verify message count increased
        get_response = await client.get(
            f"/api/v1/conversations/{conv_id}",
            headers=headers,
        )
        assert len(get_response.json()["messages"]) >= 6
        
        # 3. Pin
        pin_response = await client.put(
            f"/api/v1/conversations/{conv_id}",
            headers=headers,
            json={"is_pinned": True},
        )
        assert pin_response.json()["is_pinned"] is True
        
        # 4. Archive
        archive_response = await client.put(
            f"/api/v1/conversations/{conv_id}",
            headers=headers,
            json={"is_archived": True},
        )
        assert archive_response.json()["is_archived"] is True
        
        # 5. Search (should find in archived with flag)
        search_response = await client.get(
            "/api/v1/conversations/search?q=Lifecycle&include_archived=true",
            headers=headers,
        )
        assert search_response.status_code == 200
        
        # 6. Delete
        delete_response = await client.delete(
            f"/api/v1/conversations/{conv_id}",
            headers=headers,
        )
        assert delete_response.status_code == 200


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    @pytest.mark.asyncio
    async def test_basic_health(self, async_client):
        """Test /health endpoint."""
        response = await async_client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_full_health(self, async_client):
        """Test /health/full endpoint."""
        response = await async_client.get("/health/full")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "timestamp" in data
