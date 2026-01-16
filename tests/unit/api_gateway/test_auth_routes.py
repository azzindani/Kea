"""
Tests for authentication routes.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient


class TestAuthRoutes:
    """Tests for authentication routes."""
    
    def test_import_routes(self):
        """Test that routes can be imported."""
        from services.api_gateway.routes import auth_router
        assert auth_router is not None
    
    def test_router_has_register(self):
        """Test router has register endpoint."""
        from services.api_gateway.routes import auth_router
        
        routes = [r.path for r in auth_router.routes]
        assert "/register" in routes or any("register" in r for r in routes)
    
    def test_router_has_login(self):
        """Test router has login endpoint."""
        from services.api_gateway.routes import auth_router
        
        routes = [r.path for r in auth_router.routes]
        assert "/login" in routes or any("login" in r for r in routes)


class TestRegisterRoute:
    """Tests for register route."""
    
    @pytest.mark.asyncio
    async def test_register_schema(self):
        """Test register request schema."""
        from services.api_gateway.routes.auth import RegisterRequest
        
        request = RegisterRequest(
            email="test@example.com",
            password="password123",
            name="Test User",
        )
        
        assert request.email == "test@example.com"
        assert request.name == "Test User"


class TestLoginRoute:
    """Tests for login route."""
    
    @pytest.mark.asyncio
    async def test_login_schema(self):
        """Test login request schema."""
        from services.api_gateway.routes.auth import LoginRequest
        
        request = LoginRequest(
            email="test@example.com",
            password="password123",
        )
        
        assert request.email == "test@example.com"


class TestTokenResponse:
    """Tests for token response schema."""
    
    def test_token_response_schema(self):
        """Test token response schema."""
        from services.api_gateway.routes.auth import TokenResponse
        
        response = TokenResponse(
            access_token="access_abc",
            refresh_token="refresh_xyz",
            token_type="bearer",
        )
        
        assert response.access_token == "access_abc"
        assert response.token_type == "bearer"
