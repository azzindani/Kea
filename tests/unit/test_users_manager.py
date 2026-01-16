"""
Tests for users manager.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from shared.users import User, UserRole


class TestUser:
    """Tests for User model."""
    
    def test_create_user(self):
        """Test creating user."""
        user = User(
            user_id="user_123",
            email="test@example.com",
            name="Test User",
            role=UserRole.USER,
        )
        
        assert user.user_id == "user_123"
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.role == UserRole.USER
    
    def test_anonymous_user(self):
        """Test creating anonymous user."""
        user = User.anonymous()
        
        assert user.role == UserRole.ANONYMOUS
        assert user.email == ""
    
    def test_user_roles(self):
        """Test user role enum."""
        assert UserRole.ANONYMOUS.value == "anonymous"
        assert UserRole.USER.value == "user"
        assert UserRole.ADMIN.value == "admin"


class TestUserManager:
    """Tests for UserManager."""
    
    def test_import_manager(self):
        """Test that UserManager can be imported."""
        from shared.users.manager import UserManager, get_user_manager
        assert UserManager is not None
        assert get_user_manager is not None
    
    def test_create_manager(self):
        """Test creating user manager."""
        from shared.users.manager import UserManager
        manager = UserManager()
        assert manager is not None
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test manager initialization."""
        from shared.users.manager import UserManager
        manager = UserManager()
        await manager.initialize()
        # Should not raise


class TestAPIKeyManager:
    """Tests for APIKeyManager."""
    
    def test_import_api_key_manager(self):
        """Test that APIKeyManager can be imported."""
        from shared.users.manager import APIKeyManager, get_api_key_manager
        assert APIKeyManager is not None
        assert get_api_key_manager is not None
    
    def test_create_api_key_manager(self):
        """Test creating API key manager."""
        from shared.users.manager import APIKeyManager
        manager = APIKeyManager()
        assert manager is not None
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test manager initialization."""
        from shared.users.manager import APIKeyManager
        manager = APIKeyManager()
        await manager.initialize()
        # Should not raise
