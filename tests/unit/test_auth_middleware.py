"""
Tests for authentication middleware.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, HTTPException

from services.api_gateway.middleware.auth import (
    AuthMiddleware,
    get_current_user,
    get_current_user_required,
    require_role,
    get_optional_user,
    create_auth_middleware,
)
from shared.users import User, UserRole


class TestAuthMiddleware:
    """Tests for AuthMiddleware class."""
    
    @pytest.fixture
    def middleware(self):
        return AuthMiddleware(allow_anonymous=True)
    
    @pytest.fixture
    def strict_middleware(self):
        return AuthMiddleware(allow_anonymous=False)
    
    def test_middleware_init(self):
        """Test middleware initialization."""
        middleware = AuthMiddleware(allow_anonymous=True)
        assert middleware.allow_anonymous is True
        
        strict = AuthMiddleware(allow_anonymous=False)
        assert strict.allow_anonymous is False
    
    @pytest.mark.asyncio
    async def test_anonymous_access(self, middleware):
        """Test anonymous access when allowed."""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.cookies = {}
        request.state = MagicMock()
        
        async def call_next(req):
            return MagicMock()
        
        response = await middleware(request, call_next)
        
        # Should set anonymous user
        assert request.state.user is not None
        assert request.state.auth_method == "anonymous"


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""
    
    @pytest.mark.asyncio
    async def test_get_user_from_state(self):
        """Test getting user from request state."""
        user = User(
            user_id="user_123",
            email="test@example.com",
            name="Test User",
            role=UserRole.USER,
        )
        
        request = MagicMock(spec=Request)
        request.state.user = user
        request.headers = {}
        
        result = await get_current_user(request)
        assert result.user_id == "user_123"
    
    @pytest.mark.asyncio
    async def test_get_anonymous_user(self):
        """Test getting anonymous user when not authenticated."""
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        request.state.user = None
        request.headers = {}
        
        result = await get_current_user(request)
        assert result.role == UserRole.ANONYMOUS


class TestRequireRole:
    """Tests for require_role dependency."""
    
    @pytest.mark.asyncio
    async def test_require_admin_role(self):
        """Test requiring admin role."""
        admin_user = User(
            user_id="admin_1",
            email="admin@example.com",
            name="Admin",
            role=UserRole.ADMIN,
        )
        
        checker = require_role(UserRole.ADMIN)
        result = await checker(admin_user)
        assert result.role == UserRole.ADMIN
    
    @pytest.mark.asyncio
    async def test_require_admin_fails_for_user(self):
        """Test that regular user fails admin check."""
        regular_user = User(
            user_id="user_1",
            email="user@example.com",
            name="User",
            role=UserRole.USER,
        )
        
        checker = require_role(UserRole.ADMIN)
        
        with pytest.raises(HTTPException) as exc_info:
            await checker(regular_user)
        
        assert exc_info.value.status_code == 403


class TestGetOptionalUser:
    """Tests for get_optional_user dependency."""
    
    @pytest.mark.asyncio
    async def test_returns_user_when_authenticated(self):
        """Test returning user when authenticated."""
        user = User(
            user_id="user_1",
            email="test@example.com",
            name="Test",
            role=UserRole.USER,
        )
        
        request = MagicMock(spec=Request)
        request.state.user = user
        request.headers = {}
        
        result = await get_optional_user(request)
        assert result is not None
        assert result.user_id == "user_1"
    
    @pytest.mark.asyncio
    async def test_returns_none_for_anonymous(self):
        """Test returning None for anonymous user."""
        anon = User.anonymous()
        
        request = MagicMock(spec=Request)
        request.state.user = anon
        request.headers = {}
        
        result = await get_optional_user(request)
        assert result is None


class TestCreateAuthMiddleware:
    """Tests for create_auth_middleware factory."""
    
    def test_create_with_anonymous(self):
        """Test creating middleware with anonymous allowed."""
        middleware = create_auth_middleware(allow_anonymous=True)
        assert isinstance(middleware, AuthMiddleware)
        assert middleware.allow_anonymous is True
    
    def test_create_without_anonymous(self):
        """Test creating middleware without anonymous."""
        middleware = create_auth_middleware(allow_anonymous=False)
        assert middleware.allow_anonymous is False
