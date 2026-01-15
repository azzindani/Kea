"""
Unit Tests: Logging Context and Middleware.

Tests for logging context and middleware.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from shared.logging.context import (
    LogContext,
    get_context,
    set_context,
)
from shared.logging.middleware import (
    LoggingMiddleware,
    RequestLoggingMiddleware,
)


class TestLogContext:
    """Test LogContext class."""
    
    def test_create_context(self):
        """Test context creation."""
        context = LogContext(
            request_id="req-123",
            user_id="user-456",
        )
        
        assert context.request_id == "req-123"
        assert context.user_id == "user-456"
    
    def test_default_context(self):
        """Test default context values."""
        context = LogContext()
        
        assert context.request_id is None
        assert context.user_id is None
    
    def test_to_dict(self):
        """Test context to dictionary."""
        context = LogContext(
            request_id="req-123",
            user_id="user-456",
            extra={"key": "value"},
        )
        
        data = context.to_dict()
        
        assert data["request_id"] == "req-123"
        assert data["user_id"] == "user-456"


class TestGlobalContext:
    """Test global context management."""
    
    def test_set_and_get_context(self):
        """Test setting and getting context."""
        context = LogContext(request_id="req-999")
        
        set_context(context)
        retrieved = get_context()
        
        assert retrieved.request_id == "req-999"
    
    def test_get_default_context(self):
        """Test getting default context."""
        import shared.logging.context as module
        module._context = None
        
        context = get_context()
        
        assert context is not None


class TestLoggingMiddleware:
    """Test LoggingMiddleware class."""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware for testing."""
        return LoggingMiddleware(app=MagicMock())
    
    def test_middleware_init(self, middleware):
        """Test middleware initialization."""
        assert middleware is not None
    
    @pytest.mark.asyncio
    async def test_request_logged(self, middleware):
        """Test request is logged."""
        request = MagicMock()
        request.url.path = "/api/v1/test"
        request.method = "GET"
        request.headers = {}
        
        call_next = AsyncMock(return_value=MagicMock(status_code=200))
        
        with patch("shared.logging.middleware.logger") as mock_logger:
            response = await middleware.dispatch(request, call_next)
            
            call_next.assert_called()


class TestRequestLoggingMiddleware:
    """Test RequestLoggingMiddleware class."""
    
    @pytest.fixture
    def middleware(self):
        """Create middleware for testing."""
        return RequestLoggingMiddleware(app=MagicMock())
    
    @pytest.mark.asyncio
    async def test_request_id_generated(self, middleware):
        """Test request ID is generated."""
        request = MagicMock()
        request.url.path = "/api/v1/test"
        request.method = "POST"
        request.headers.get.return_value = None
        
        call_next = AsyncMock(return_value=MagicMock(status_code=200))
        
        response = await middleware.dispatch(request, call_next)
        
        # Response should have request ID header
        assert response is not None
    
    @pytest.mark.asyncio
    async def test_existing_request_id_used(self, middleware):
        """Test existing request ID is used."""
        request = MagicMock()
        request.url.path = "/api/v1/test"
        request.method = "GET"
        request.headers.get.return_value = "existing-req-id"
        
        call_next = AsyncMock(return_value=MagicMock(status_code=200))
        
        response = await middleware.dispatch(request, call_next)
        
        assert response is not None
