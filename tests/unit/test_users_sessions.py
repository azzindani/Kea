"""
Unit Tests: User and Session Management.

Tests for user models, password hashing, and session management.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from shared.users.models import User, APIKey, UserRole
from shared.sessions.manager import SessionManager, TokenPair


class TestUserModel:
    """Test User model."""
    
    def test_create_user(self):
        """Test user creation."""
        user = User(
            email="test@example.com",
            name="Test User",
        )
        
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.role == UserRole.USER
        assert user.is_active is True
    
    def test_user_id_generated(self):
        """Test user ID is generated."""
        user = User(email="test@example.com", name="Test")
        
        assert user.user_id is not None
        assert len(user.user_id) == 36  # UUID format
    
    def test_password_hashing(self):
        """Test password is hashed correctly."""
        user = User(email="test@example.com", name="Test")
        user.set_password("SecurePassword123!")
        
        assert user.password_hash != "SecurePassword123!"
        assert user.password_hash.startswith("$2b$")  # bcrypt format
    
    def test_password_verification(self):
        """Test password verification."""
        user = User(email="test@example.com", name="Test")
        user.set_password("SecurePassword123!")
        
        assert user.verify_password("SecurePassword123!") is True
        assert user.verify_password("WrongPassword") is False
    
    def test_admin_role(self):
        """Test admin role."""
        user = User(
            email="admin@example.com",
            name="Admin",
            role=UserRole.ADMIN,
        )
        
        assert user.role == UserRole.ADMIN
        assert user.is_admin is True
    
    def test_tenant_id(self):
        """Test tenant ID assignment."""
        user = User(
            email="test@example.com",
            name="Test",
            tenant_id="tenant-123",
        )
        
        assert user.tenant_id == "tenant-123"
    
    def test_to_dict(self):
        """Test dictionary serialization."""
        user = User(
            email="test@example.com",
            name="Test User",
        )
        
        data = user.to_dict()
        
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert "password_hash" not in data  # Should not expose


class TestAPIKeyModel:
    """Test API Key model."""
    
    def test_create_api_key(self):
        """Test API key creation."""
        key = APIKey.create(
            user_id="user-123",
            name="Test Key",
        )
        
        assert key.user_id == "user-123"
        assert key.name == "Test Key"
        assert key.raw_key is not None
        assert key.raw_key.startswith("kea_")
    
    def test_key_prefix_stored(self):
        """Test key prefix is stored."""
        key = APIKey.create(user_id="user-123", name="Test")
        
        assert key.key_prefix is not None
        assert len(key.key_prefix) == 8
        assert key.raw_key.startswith(f"kea_{key.key_prefix}")
    
    def test_key_hash_stored(self):
        """Test key hash is stored."""
        key = APIKey.create(user_id="user-123", name="Test")
        
        assert key.key_hash is not None
        assert key.key_hash != key.raw_key
    
    def test_verify_key(self):
        """Test API key verification."""
        key = APIKey.create(user_id="user-123", name="Test")
        raw_key = key.raw_key
        
        assert key.verify(raw_key) is True
        assert key.verify("wrong_key") is False
    
    def test_key_expiration(self):
        """Test expired key detection."""
        key = APIKey.create(
            user_id="user-123",
            name="Test",
            expires_at=datetime.utcnow() - timedelta(days=1),
        )
        
        assert key.is_expired is True
    
    def test_key_not_expired(self):
        """Test valid key detection."""
        key = APIKey.create(
            user_id="user-123",
            name="Test",
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        
        assert key.is_expired is False


class TestSessionManager:
    """Test session management."""
    
    @pytest.fixture
    def session_manager(self):
        """Create session manager with mock settings."""
        with patch("shared.sessions.manager.get_settings") as mock:
            mock.return_value.jwt_secret = "test-secret-key-at-least-32-chars!"
            mock.return_value.jwt_algorithm = "HS256"
            return SessionManager()
    
    def test_create_token_pair(self, session_manager):
        """Test token pair creation."""
        tokens = session_manager.create_token_pair(
            user_id="user-123",
            email="test@example.com",
        )
        
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"
    
    def test_verify_access_token(self, session_manager):
        """Test access token verification."""
        tokens = session_manager.create_token_pair(
            user_id="user-123",
            email="test@example.com",
        )
        
        payload = session_manager.verify_access_token(tokens.access_token)
        
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["email"] == "test@example.com"
    
    def test_invalid_token_rejected(self, session_manager):
        """Test invalid token is rejected."""
        result = session_manager.verify_access_token("invalid.token.here")
        
        assert result is None
    
    def test_refresh_token_contains_different_claims(self, session_manager):
        """Test refresh token has different expiry."""
        tokens = session_manager.create_token_pair(
            user_id="user-123",
            email="test@example.com",
        )
        
        access_payload = session_manager.verify_access_token(tokens.access_token)
        refresh_payload = session_manager.verify_refresh_token(tokens.refresh_token)
        
        # Refresh token should have longer expiry
        assert refresh_payload["exp"] > access_payload["exp"]


class TestUserRole:
    """Test user roles."""
    
    def test_user_role(self):
        """Test default user role."""
        assert UserRole.USER.value == "user"
    
    def test_admin_role(self):
        """Test admin role."""
        assert UserRole.ADMIN.value == "admin"
    
    def test_service_role(self):
        """Test service account role."""
        assert UserRole.SERVICE.value == "service"
