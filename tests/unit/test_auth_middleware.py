"""
Unit Tests: Auth Middleware.

Tests for authentication middleware.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from services.api_gateway.middleware.auth import (
    AuthMiddleware,
    get_current_user,
    get_optional_user,
    require_admin,
)


class TestAuthMiddleware:
    """Test AuthMiddleware class."""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware for testing."""
        return AuthMiddleware(app=MagicMock())
    
    def test_middleware_init(self, middleware):
        """Test middleware initialization."""
        assert middleware is not None
    
    @pytest.mark.asyncio
    async def test_exempt_path_bypassed(self, middleware):
        """Test exempt paths bypass auth."""
        request = MagicMock()
        request.url.path = "/health"
        
        call_next = AsyncMock(return_value=MagicMock())
        
        response = await middleware.dispatch(request, call_next)
        
        call_next.assert_called()
    
    @pytest.mark.asyncio
    async def test_bearer_token_extracted(self, middleware):
        """Test Bearer token extraction."""
        request = MagicMock()
        request.url.path = "/api/v1/conversations"
        request.headers.get.return_value = "Bearer valid.token.here"
        
        with patch.object(middleware, "_validate_token") as mock:
            mock.return_value = {"sub": "user-123"}
            
            call_next = AsyncMock(return_value=MagicMock())
            await middleware.dispatch(request, call_next)
    
    @pytest.mark.asyncio
    async def test_api_key_extracted(self, middleware):
        """Test API key extraction."""
        request = MagicMock()
        request.url.path = "/api/v1/conversations"
        request.headers.get.side_effect = lambda h: "kea_abc123" if h == "X-API-Key" else None
        
        with patch.object(middleware, "_validate_api_key") as mock:
            mock.return_value = MagicMock()
            
            call_next = AsyncMock(return_value=MagicMock())
            await middleware.dispatch(request, call_next)


class TestGetCurrentUser:
    """Test get_current_user dependency."""
    
    @pytest.mark.asyncio
    async def test_returns_user_from_state(self):
        """Test returns user from request state."""
        request = MagicMock()
        request.state.user = MagicMock(user_id="user-123")
        
        user = await get_current_user(request)
        
        assert user.user_id == "user-123"
    
    @pytest.mark.asyncio
    async def test_raises_without_user(self):
        """Test raises 401 without user."""
        from fastapi import HTTPException
        
        request = MagicMock()
        request.state.user = None
        
        with pytest.raises(HTTPException) as exc:
            await get_current_user(request)
        
        assert exc.value.status_code == 401


class TestGetOptionalUser:
    """Test get_optional_user dependency."""
    
    @pytest.mark.asyncio
    async def test_returns_user_if_present(self):
        """Test returns user if present."""
        request = MagicMock()
        request.state.user = MagicMock(user_id="user-123")
        
        user = await get_optional_user(request)
        
        assert user.user_id == "user-123"
    
    @pytest.mark.asyncio
    async def test_returns_none_if_absent(self):
        """Test returns None if no user."""
        request = MagicMock()
        request.state.user = None
        
        user = await get_optional_user(request)
        
        assert user is None


class TestRequireAdmin:
    """Test require_admin dependency."""
    
    @pytest.mark.asyncio
    async def test_passes_for_admin(self):
        """Test passes for admin user."""
        from shared.users.models import UserRole
        
        user = MagicMock()
        user.role = UserRole.ADMIN
        
        result = await require_admin(user)
        
        assert result == user
    
    @pytest.mark.asyncio
    async def test_raises_for_non_admin(self):
        """Test raises 403 for non-admin."""
        from fastapi import HTTPException
        from shared.users.models import UserRole
        
        user = MagicMock()
        user.role = UserRole.USER
        
        with pytest.raises(HTTPException) as exc:
            await require_admin(user)
        
        assert exc.value.status_code == 403
