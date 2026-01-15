"""
Unit Tests: API Routes - Auth.

Tests for authentication routes.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient

from services.api_gateway.main import app


class TestRegisterRoute:
    """Test register endpoint."""
    
    @pytest.mark.asyncio
    async def test_register_success(self):
        """Test successful registration."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("services.api_gateway.routes.auth.user_manager") as mock:
                mock.get_by_email = AsyncMock(return_value=None)
                mock.create = AsyncMock(return_value=MagicMock(
                    user_id="user-123",
                    email="new@example.com",
                ))
                
                with patch("services.api_gateway.routes.auth.session_manager") as mock_session:
                    mock_session.create_token_pair.return_value = MagicMock(
                        access_token="access",
                        refresh_token="refresh",
                        token_type="bearer",
                        expires_in=3600,
                    )
                    
                    response = await client.post(
                        "/api/v1/auth/register",
                        json={
                            "email": "new@example.com",
                            "name": "New User",
                            "password": "SecurePass123!",
                        },
                    )
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self):
        """Test registration with duplicate email."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("services.api_gateway.routes.auth.user_manager") as mock:
                mock.get_by_email = AsyncMock(return_value=MagicMock())
                
                response = await client.post(
                    "/api/v1/auth/register",
                    json={
                        "email": "existing@example.com",
                        "name": "User",
                        "password": "SecurePass123!",
                    },
                )
                
                assert response.status_code == 400


class TestLoginRoute:
    """Test login endpoint."""
    
    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test successful login."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("services.api_gateway.routes.auth.user_manager") as mock:
                mock.authenticate = AsyncMock(return_value=MagicMock(
                    user_id="user-123",
                    email="user@example.com",
                ))
                
                with patch("services.api_gateway.routes.auth.session_manager") as mock_session:
                    mock_session.create_token_pair.return_value = MagicMock(
                        access_token="access",
                        refresh_token="refresh",
                        token_type="bearer",
                        expires_in=3600,
                    )
                    
                    response = await client.post(
                        "/api/v1/auth/login",
                        json={
                            "email": "user@example.com",
                            "password": "password123",
                        },
                    )
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("services.api_gateway.routes.auth.user_manager") as mock:
                mock.authenticate = AsyncMock(return_value=None)
                
                response = await client.post(
                    "/api/v1/auth/login",
                    json={
                        "email": "user@example.com",
                        "password": "wrongpassword",
                    },
                )
                
                assert response.status_code == 401


class TestLogoutRoute:
    """Test logout endpoint."""
    
    @pytest.mark.asyncio
    async def test_logout(self):
        """Test logout clears session."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("services.api_gateway.middleware.auth.AuthMiddleware._validate_token") as mock:
                mock.return_value = {"sub": "user-123"}
                
                with patch("services.api_gateway.routes.auth.session_manager") as mock_session:
                    mock_session.invalidate_session = AsyncMock()
                    
                    response = await client.post(
                        "/api/v1/auth/logout",
                        headers={"Authorization": "Bearer valid.token"},
                    )


class TestRefreshRoute:
    """Test token refresh endpoint."""
    
    @pytest.mark.asyncio
    async def test_refresh_token(self):
        """Test refreshing access token."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("services.api_gateway.routes.auth.session_manager") as mock:
                mock.refresh_tokens.return_value = MagicMock(
                    access_token="new_access",
                    refresh_token="new_refresh",
                    token_type="bearer",
                    expires_in=3600,
                )
                
                response = await client.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": "valid_refresh_token"},
                )
