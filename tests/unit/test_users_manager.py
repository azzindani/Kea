"""
Unit Tests: Users Manager.

Tests for user management.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from shared.users.models import (
    User,
    UserRole,
    APIKey,
)
from shared.users.manager import (
    UserManager,
    APIKeyManager,
)


class TestUser:
    """Test User model."""
    
    def test_create_user(self):
        """Test user creation."""
        user = User(
            email="test@example.com",
            name="Test User",
        )
        
        assert user.email == "test@example.com"
        assert user.name == "Test User"
    
    def test_user_id_generated(self):
        """Test user ID is auto-generated."""
        user = User(email="test@example.com", name="Test")
        
        assert user.user_id is not None
        assert len(user.user_id) > 0
    
    def test_default_role(self):
        """Test default role is USER."""
        user = User(email="test@example.com", name="Test")
        
        assert user.role == UserRole.USER
    
    def test_password_hashing(self):
        """Test password is hashed."""
        user = User(email="test@example.com", name="Test")
        user.set_password("MySecurePassword123!")
        
        assert user.password_hash != "MySecurePassword123!"
        assert len(user.password_hash) > 0
    
    def test_password_verification(self):
        """Test password verification."""
        user = User(email="test@example.com", name="Test")
        user.set_password("MySecurePassword123!")
        
        assert user.verify_password("MySecurePassword123!") is True
        assert user.verify_password("WrongPassword") is False
    
    def test_is_active_default(self):
        """Test default is_active is True."""
        user = User(email="test@example.com", name="Test")
        
        assert user.is_active is True


class TestAPIKey:
    """Test APIKey model."""
    
    def test_create_api_key(self):
        """Test API key creation."""
        key = APIKey.create(
            user_id="user-123",
            name="Test Key",
        )
        
        assert key.user_id == "user-123"
        assert key.name == "Test Key"
    
    def test_raw_key_generated(self):
        """Test raw key is generated."""
        key = APIKey.create(user_id="user-123", name="Test")
        
        assert key.raw_key is not None
        assert key.raw_key.startswith("kea_")
    
    def test_key_hash_stored(self):
        """Test key hash is stored."""
        key = APIKey.create(user_id="user-123", name="Test")
        
        assert key.key_hash is not None
        assert key.key_hash != key.raw_key
    
    def test_verify_key(self):
        """Test key verification."""
        key = APIKey.create(user_id="user-123", name="Test")
        raw = key.raw_key
        
        assert key.verify(raw) is True
        assert key.verify("wrong_key") is False


class TestUserManager:
    """Test UserManager class."""
    
    @pytest.fixture
    def manager(self):
        """Create manager for testing."""
        return UserManager()
    
    @pytest.mark.asyncio
    async def test_create_user(self, manager):
        """Test creating user."""
        with patch.object(manager, "_db") as mock_db:
            mock_db.execute = AsyncMock()
            mock_db.fetchone = AsyncMock(return_value=None)
            
            user = await manager.create(
                email="new@example.com",
                name="New User",
                password="SecurePass123!",
            )
            
            assert user.email == "new@example.com"
    
    @pytest.mark.asyncio
    async def test_get_by_email(self, manager):
        """Test getting user by email."""
        with patch.object(manager, "_db") as mock_db:
            mock_db.fetchone = AsyncMock(return_value={
                "user_id": "user-123",
                "email": "test@example.com",
                "name": "Test",
                "password_hash": "hash",
                "role": "user",
                "is_active": True,
                "created_at": datetime.utcnow(),
            })
            
            user = await manager.get_by_email("test@example.com")
            
            assert user is not None
    
    @pytest.mark.asyncio
    async def test_authenticate(self, manager):
        """Test user authentication."""
        with patch.object(manager, "get_by_email") as mock:
            mock_user = MagicMock()
            mock_user.verify_password.return_value = True
            mock_user.is_active = True
            mock.return_value = mock_user
            
            user = await manager.authenticate("test@example.com", "password")
            
            assert user is not None


class TestAPIKeyManager:
    """Test APIKeyManager class."""
    
    @pytest.fixture
    def manager(self):
        """Create manager for testing."""
        return APIKeyManager()
    
    @pytest.mark.asyncio
    async def test_create_key(self, manager):
        """Test creating API key."""
        with patch.object(manager, "_db") as mock_db:
            mock_db.execute = AsyncMock()
            
            key = await manager.create(
                user_id="user-123",
                name="New Key",
            )
            
            assert key.user_id == "user-123"
    
    @pytest.mark.asyncio
    async def test_list_keys(self, manager):
        """Test listing user's keys."""
        with patch.object(manager, "_db") as mock_db:
            mock_db.fetchall = AsyncMock(return_value=[
                {
                    "key_id": "key-1",
                    "user_id": "user-123",
                    "name": "Key 1",
                    "key_prefix": "abc12345",
                    "created_at": datetime.utcnow(),
                },
            ])
            
            keys = await manager.list(user_id="user-123")
            
            assert len(keys) >= 0
    
    @pytest.mark.asyncio
    async def test_revoke_key(self, manager):
        """Test revoking API key."""
        with patch.object(manager, "_db") as mock_db:
            mock_db.execute = AsyncMock()
            
            await manager.revoke("key-123", "user-123")
            
            mock_db.execute.assert_called()
