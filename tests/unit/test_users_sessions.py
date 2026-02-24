"""
Tests for users and sessions module.
"""


import pytest


class TestUserImports:
    """Test importing user classes."""

    def test_import_user(self):
        """Test importing User class."""
        from shared.users import User, UserRole
        assert User is not None
        assert UserRole is not None

    def test_import_manager(self):
        """Test importing UserManager."""
        from shared.users.manager import UserManager, get_user_manager
        assert UserManager is not None
        assert get_user_manager is not None


class TestUser:
    """Test User class."""

    def test_create_user(self):
        """Test creating user."""
        from shared.users import User, UserRole

        user = User(
            user_id="user_123",
            email="test@example.com",
            name="Test User",
            role=UserRole.USER,
        )

        assert user.user_id == "user_123"
        assert user.email == "test@example.com"

    def test_anonymous_user(self):
        """Test anonymous user creation."""
        from shared.users import User, UserRole

        user = User.anonymous()
        assert user.role == UserRole.ANONYMOUS


class TestUserManager:
    """Test UserManager class."""

    def test_create_manager(self):
        """Test creating manager."""
        from shared.users.manager import UserManager

        manager = UserManager()
        assert manager is not None

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test manager initialization."""
        from shared.users.manager import UserManager

        manager = UserManager()
        await manager.initialize()
        # Initialization should succeed (may use SQLite or PostgreSQL)


class TestSessionImports:
    """Test importing session classes."""

    def test_import_session(self):
        """Test importing Session class."""
        from shared.sessions.manager import Session, SessionManager
        assert Session is not None
        assert SessionManager is not None

    def test_import_jwt(self):
        """Test importing JWT manager."""
        from shared.sessions.manager import JWTManager, get_jwt_manager
        assert JWTManager is not None
        assert get_jwt_manager is not None


class TestSession:
    """Test Session class."""

    def test_create_session(self):
        """Test creating session."""
        from shared.sessions.manager import Session

        session = Session(
            session_id="sess_123",
            user_id="user_456",
        )

        assert session.session_id == "sess_123"
        assert session.user_id == "user_456"
        assert session.is_active is True
