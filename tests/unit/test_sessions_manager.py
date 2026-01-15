"""
Unit Tests: Sessions Manager.

Tests for session and JWT token management.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

from shared.sessions.manager import (
    SessionManager,
    Session,
    TokenPair,
)


class TestSession:
    """Test Session model."""
    
    def test_create_session(self):
        """Test session creation."""
        session = Session(
            session_id="sess-123",
            user_id="user-123",
        )
        
        assert session.session_id == "sess-123"
        assert session.user_id == "user-123"
    
    def test_session_defaults(self):
        """Test session default values."""
        session = Session(
            session_id="sess-123",
            user_id="user-123",
        )
        
        assert session.is_active is True
        assert session.ip_address is None
    
    def test_session_expiry(self):
        """Test session expiry detection."""
        # Expired session
        session = Session(
            session_id="sess-123",
            user_id="user-123",
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        
        assert session.is_expired is True
    
    def test_session_not_expired(self):
        """Test session not expired."""
        session = Session(
            session_id="sess-123",
            user_id="user-123",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        
        assert session.is_expired is False


class TestTokenPair:
    """Test TokenPair model."""
    
    def test_token_pair(self):
        """Test token pair creation."""
        pair = TokenPair(
            access_token="access.token.here",
            refresh_token="refresh.token.here",
            token_type="bearer",
            expires_in=3600,
        )
        
        assert pair.access_token == "access.token.here"
        assert pair.refresh_token == "refresh.token.here"
        assert pair.token_type == "bearer"
        assert pair.expires_in == 3600


class TestSessionManager:
    """Test SessionManager class."""
    
    @pytest.fixture
    def manager(self):
        """Create manager for testing."""
        with patch("shared.sessions.manager.get_settings") as mock:
            mock.return_value.jwt_secret = "test-secret-key-32-chars-minimum!"
            mock.return_value.jwt_algorithm = "HS256"
            mock.return_value.access_token_expire_minutes = 30
            mock.return_value.refresh_token_expire_days = 7
            return SessionManager()
    
    def test_create_access_token(self, manager):
        """Test creating access token."""
        token = manager.create_access_token(
            user_id="user-123",
            email="test@example.com",
        )
        
        assert token is not None
        assert len(token) > 0
    
    def test_create_refresh_token(self, manager):
        """Test creating refresh token."""
        token = manager.create_refresh_token(
            user_id="user-123",
        )
        
        assert token is not None
        assert len(token) > 0
    
    def test_create_token_pair(self, manager):
        """Test creating token pair."""
        pair = manager.create_token_pair(
            user_id="user-123",
            email="test@example.com",
        )
        
        assert pair.access_token is not None
        assert pair.refresh_token is not None
        assert pair.token_type == "bearer"
    
    def test_verify_access_token(self, manager):
        """Test verifying valid access token."""
        token = manager.create_access_token(
            user_id="user-123",
            email="test@example.com",
        )
        
        payload = manager.verify_access_token(token)
        
        assert payload is not None
        assert payload["sub"] == "user-123"
    
    def test_verify_invalid_token(self, manager):
        """Test verifying invalid token."""
        result = manager.verify_access_token("invalid.token.here")
        
        assert result is None
    
    def test_verify_refresh_token(self, manager):
        """Test verifying refresh token."""
        token = manager.create_refresh_token(user_id="user-123")
        
        payload = manager.verify_refresh_token(token)
        
        assert payload is not None
        assert payload["sub"] == "user-123"
    
    def test_refresh_tokens(self, manager):
        """Test refreshing tokens."""
        refresh_token = manager.create_refresh_token(user_id="user-123")
        
        new_pair = manager.refresh_tokens(refresh_token)
        
        assert new_pair is not None
        assert new_pair.access_token is not None


class TestSessionStorage:
    """Test session storage operations."""
    
    @pytest.fixture
    def manager(self):
        """Create manager with mocked storage."""
        with patch("shared.sessions.manager.get_settings") as mock:
            mock.return_value.jwt_secret = "test-secret-key-32-chars-minimum!"
            mock.return_value.jwt_algorithm = "HS256"
            return SessionManager()
    
    @pytest.mark.asyncio
    async def test_create_session(self, manager):
        """Test creating session in storage."""
        with patch.object(manager, "_db") as mock_db:
            mock_db.execute = AsyncMock()
            
            session = await manager.create_session(
                user_id="user-123",
                ip_address="192.168.1.1",
            )
            
            assert session.user_id == "user-123"
    
    @pytest.mark.asyncio
    async def test_invalidate_session(self, manager):
        """Test invalidating session."""
        with patch.object(manager, "_db") as mock_db:
            mock_db.execute = AsyncMock()
            
            await manager.invalidate_session("sess-123")
            
            mock_db.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_invalidate_all_sessions(self, manager):
        """Test invalidating all user sessions."""
        with patch.object(manager, "_db") as mock_db:
            mock_db.execute = AsyncMock()
            
            await manager.invalidate_all_sessions("user-123")
            
            mock_db.execute.assert_called()
