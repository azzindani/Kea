"""
Tests for session management.
"""

from datetime import datetime, timedelta

import pytest

from shared.sessions.manager import (
    JWTManager,
    Session,
    SessionManager,
)


class TestSession:
    """Tests for Session dataclass."""

    def test_session_creation(self):
        """Test session creation."""
        session = Session(
            session_id="sess_123",
            user_id="user_456",
            tenant_id="default",
        )
        assert session.session_id == "sess_123"
        assert session.user_id == "user_456"
        assert session.is_active is True

    def test_session_expiration(self):
        """Test session expiration check."""
        # Not expired
        session = Session(
            session_id="sess_1",
            user_id="user_1",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        assert session.is_expired() is False

        # Expired
        expired_session = Session(
            session_id="sess_2",
            user_id="user_2",
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        assert expired_session.is_expired() is True

    def test_session_touch(self):
        """Test updating last activity."""
        session = Session(
            session_id="sess_1",
            user_id="user_1",
        )
        old_activity = session.last_activity
        session.touch()
        assert session.last_activity >= old_activity

    def test_session_to_dict(self):
        """Test session serialization."""
        session = Session(
            session_id="sess_1",
            user_id="user_1",
            tenant_id="tenant_1",
        )
        data = session.to_dict()
        assert data["session_id"] == "sess_1"
        assert data["user_id"] == "user_1"
        assert data["tenant_id"] == "tenant_1"


class TestSessionManager:
    """Tests for SessionManager."""

    @pytest.fixture
    def manager(self):
        return SessionManager(session_hours=1)

    @pytest.mark.asyncio
    async def test_create_session(self, manager):
        """Test session creation."""
        session = await manager.create_session(
            user_id="user_123",
            tenant_id="default",
            device_info="Chrome",
            ip_address="127.0.0.1",
        )
        assert session.user_id == "user_123"
        assert session.device_info == "Chrome"
        assert session.ip_address == "127.0.0.1"

    @pytest.mark.asyncio
    async def test_get_session(self, manager):
        """Test getting session by ID."""
        session = await manager.create_session(user_id="user_1")
        retrieved = await manager.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.user_id == "user_1"

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, manager):
        """Test getting non-existent session."""
        result = await manager.get_session("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_end_session(self, manager):
        """Test ending session."""
        session = await manager.create_session(user_id="user_1")
        await manager.end_session(session.session_id)
        result = await manager.get_session(session.session_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_sessions(self, manager):
        """Test getting all sessions for a user."""
        await manager.create_session(user_id="user_1")
        await manager.create_session(user_id="user_1")
        await manager.create_session(user_id="user_2")

        sessions = await manager.get_user_sessions("user_1")
        assert len(sessions) == 2

    @pytest.mark.asyncio
    async def test_refresh_session(self, manager):
        """Test refreshing session."""
        session = await manager.create_session(user_id="user_1")
        old_expires = session.expires_at

        await manager.refresh_session(session.session_id)
        refreshed = await manager.get_session(session.session_id)

        assert refreshed.expires_at > old_expires


class TestJWTManager:
    """Tests for JWTManager."""

    @pytest.fixture
    def jwt_manager(self):
        return JWTManager(
            secret_key="test_secret_key_12345",
            access_token_minutes=60,
            refresh_token_days=7,
        )

    def test_create_access_token(self, jwt_manager):
        """Test access token creation."""
        token = jwt_manager.create_access_token(
            user_id="user_123",
            tenant_id="default",
            role="user",
        )
        assert token is not None
        assert isinstance(token, str)

    def test_verify_access_token(self, jwt_manager):
        """Test access token verification."""
        token = jwt_manager.create_access_token(user_id="user_123")
        payload = jwt_manager.verify_token(token)

        assert payload is not None
        assert payload["sub"] == "user_123"
        assert payload["type"] == "access"

    def test_create_refresh_token(self, jwt_manager):
        """Test refresh token creation."""
        token = jwt_manager.create_refresh_token(user_id="user_123")
        assert token is not None

        payload = jwt_manager.verify_token(token)
        assert payload["type"] == "refresh"

    def test_create_tokens(self, jwt_manager):
        """Test creating both access and refresh tokens."""
        tokens = jwt_manager.create_tokens(
            user_id="user_123",
            tenant_id="tenant_1",
            role="admin",
        )
        assert "access_token" in tokens
        assert "refresh_token" in tokens

    def test_invalid_token(self, jwt_manager):
        """Test verifying invalid token."""
        payload = jwt_manager.verify_token("invalid_token")
        assert payload is None

    def test_expired_token(self, jwt_manager):
        """Test verifying expired token."""
        # Create manager with 0 minute expiry
        short_jwt = JWTManager(
            secret_key="test",
            access_token_minutes=0,
        )
        token = short_jwt.create_access_token(user_id="user_1")

        # Token should be expired immediately
        payload = short_jwt.verify_token(token)
        assert payload is None
