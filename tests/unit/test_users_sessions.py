"""
Tests for users and sessions integration.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

from shared.users import User, UserRole
from shared.users.manager import UserManager, APIKeyManager
from shared.sessions.manager import Session, SessionManager, JWTManager


class TestUserModel:
    """Tests for User model."""
    
    def test_user_creation(self):
        """Test creating user."""
        user = User(
            user_id="user_123",
            email="test@example.com",
            name="Test User",
            role=UserRole.USER,
            tenant_id="default",
        )
        assert user.user_id == "user_123"
        assert user.email == "test@example.com"
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
    
    @pytest.fixture
    def manager(self):
        return UserManager()
    
    @pytest.mark.asyncio
    async def test_initialize(self, manager):
        """Test manager initialization."""
        await manager.initialize()
        assert manager._use_postgres is False  # Should fallback to SQLite
    
    @pytest.mark.asyncio
    async def test_create_user(self, manager):
        """Test creating user."""
        await manager.initialize()
        
        user = await manager.create_user(
            email="newuser@example.com",
            name="New User",
            password="test123",
        )
        
        assert user.email == "newuser@example.com"
        assert user.name == "New User"
    
    @pytest.mark.asyncio
    async def test_get_by_email(self, manager):
        """Test getting user by email."""
        await manager.initialize()
        
        await manager.create_user(
            email="findme@example.com",
            name="Find Me",
        )
        
        user = await manager.get_by_email("findme@example.com")
        assert user is not None
        assert user.name == "Find Me"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_user(self, manager):
        """Test getting non-existent user."""
        await manager.initialize()
        
        user = await manager.get_by_email("noone@example.com")
        assert user is None


class TestSession:
    """Tests for Session model."""
    
    def test_session_creation(self):
        """Test session creation."""
        session = Session(
            session_id="sess_123",
            user_id="user_456",
        )
        assert session.session_id == "sess_123"
        assert session.user_id == "user_456"
    
    def test_session_expiration(self):
        """Test session expiration."""
        expired = Session(
            session_id="sess_1",
            user_id="user_1",
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        assert expired.is_expired() is True
        
        valid = Session(
            session_id="sess_2",
            user_id="user_2",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        assert valid.is_expired() is False


class TestJWTIntegration:
    """Tests for JWT and session integration."""
    
    @pytest.fixture
    def jwt_manager(self):
        return JWTManager(secret_key="test_secret")
    
    @pytest.fixture
    def session_manager(self):
        return SessionManager()
    
    @pytest.mark.asyncio
    async def test_full_auth_flow(self, jwt_manager, session_manager):
        """Test full authentication flow."""
        # 1. Create session
        session = await session_manager.create_session(
            user_id="user_123",
            device_info="Test Browser",
        )
        assert session is not None
        
        # 2. Create tokens
        tokens = jwt_manager.create_tokens(
            user_id="user_123",
            tenant_id="default",
            role="user",
        )
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        
        # 3. Verify access token
        payload = jwt_manager.verify_token(tokens["access_token"])
        assert payload["sub"] == "user_123"
        
        # 4. End session
        await session_manager.end_session(session.session_id)
        ended = await session_manager.get_session(session.session_id)
        assert ended is None
