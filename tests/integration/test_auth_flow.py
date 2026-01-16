"""
Integration Tests: Authentication Flow.

Tests for register, login, logout, token refresh, and API key flow.
"""

import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from services.api_gateway.main import app


@pytest.fixture
def test_user():
    """Test user data with unique email."""
    unique_id = str(uuid.uuid4())[:8]
    return {
        "email": f"test_{unique_id}@example.com",
        "name": "Test User",
        "password": "SecurePassword123!",
    }


@pytest.fixture
async def async_client():
    """Create async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestAuthRegistration:
    """Test user registration."""
    
    @pytest.mark.asyncio
    async def test_register_success(self, async_client, test_user):
        """Test successful registration."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json=test_user,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == test_user["email"]
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, async_client, test_user):
        """Test duplicate email rejection."""
        # First registration
        await async_client.post("/api/v1/auth/register", json=test_user)
        
        # Duplicate
        response = await async_client.post(
            "/api/v1/auth/register",
            json=test_user,
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_register_weak_password(self, async_client):
        """Test weak password rejection."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "name": "Weak",
                "password": "123",  # Too short
            },
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_register_invalid_email(self, async_client):
        """Test invalid email rejection."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "name": "Invalid",
                "password": "SecurePassword123!",
            },
        )
        
        assert response.status_code == 422


class TestAuthLogin:
    """Test user login."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, async_client, test_user):
        """Test successful login."""
        # Register first
        await async_client.post("/api/v1/auth/register", json=test_user)
        
        # Login
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert "session_id" in response.cookies
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, async_client, test_user):
        """Test wrong password rejection."""
        # Register first
        await async_client.post("/api/v1/auth/register", json=test_user)
        
        # Login with wrong password
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": "WrongPassword!",
            },
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, async_client):
        """Test nonexistent user rejection."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "noone@example.com",
                "password": "SomePassword!",
            },
        )
        
        assert response.status_code == 401


class TestAuthToken:
    """Test token operations."""
    
    @pytest.mark.asyncio
    async def test_token_refresh(self, async_client, test_user):
        """Test token refresh."""
        # Register
        reg_response = await async_client.post(
            "/api/v1/auth/register",
            json=test_user,
        )
        refresh_token = reg_response.json()["refresh_token"]
        
        # Refresh
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
    
    @pytest.mark.asyncio
    async def test_token_refresh_invalid(self, async_client):
        """Test invalid refresh token rejection."""
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_access_protected_route(self, async_client, test_user):
        """Test accessing protected route with token."""
        # Register
        reg_response = await async_client.post(
            "/api/v1/auth/register",
            json=test_user,
        )
        access_token = reg_response.json()["access_token"]
        
        # Access /me
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        assert response.status_code == 200
        assert response.json()["email"] == test_user["email"]
    
    @pytest.mark.asyncio
    async def test_access_protected_route_no_token(self, async_client):
        """Test protected route without token."""
        response = await async_client.get("/api/v1/auth/me")
        
        assert response.status_code == 401


class TestAuthLogout:
    """Test logout."""
    
    @pytest.mark.asyncio
    async def test_logout(self, async_client, test_user):
        """Test logout invalidates session."""
        # Register and get token
        reg_response = await async_client.post(
            "/api/v1/auth/register",
            json=test_user,
        )
        access_token = reg_response.json()["access_token"]
        
        # Logout
        response = await async_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        assert response.status_code == 200
        assert "session_id" not in response.cookies or response.cookies["session_id"] == ""


class TestAPIKeyAuth:
    """Test API key authentication."""
    
    @pytest.mark.asyncio
    async def test_create_api_key(self, async_client, test_user):
        """Test API key creation."""
        # Register
        reg_response = await async_client.post(
            "/api/v1/auth/register",
            json=test_user,
        )
        access_token = reg_response.json()["access_token"]
        
        # Create API key
        response = await async_client.post(
            "/api/v1/users/me/keys",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Test Key"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "raw_key" in data  # Only shown once
        assert data["raw_key"].startswith("kea_")
    
    @pytest.mark.asyncio
    async def test_access_with_api_key(self, async_client, test_user):
        """Test accessing protected route with API key."""
        # Register
        reg_response = await async_client.post(
            "/api/v1/auth/register",
            json=test_user,
        )
        access_token = reg_response.json()["access_token"]
        
        # Create API key
        key_response = await async_client.post(
            "/api/v1/users/me/keys",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": "Test Key"},
        )
        api_key = key_response.json()["raw_key"]
        
        # Access with API key
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"X-API-Key": api_key},
        )
        
        assert response.status_code == 200
        assert response.json()["email"] == test_user["email"]
