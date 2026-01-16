"""
Tests for authentication routes.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestAuthRoutes:
    """Tests for authentication routes."""
    
    def test_import_routes(self):
        """Test that auth routes can be imported."""
        from services.api_gateway.routes.auth import router
        assert router is not None
    
    def test_router_has_endpoints(self):
        """Test router has endpoints."""
        from services.api_gateway.routes.auth import router
        
        routes = [r.path for r in router.routes]
        # Should have some routes defined
        assert len(routes) > 0


class TestRegisterRequest:
    """Tests for register request schema."""
    
    def test_register_schema(self):
        """Test register request schema."""
        from services.api_gateway.routes.auth import RegisterRequest
        
        request = RegisterRequest(
            email="test@example.com",
            password="password123",
            name="Test User",
        )
        
        assert request.email == "test@example.com"
        assert request.name == "Test User"


class TestLoginRequest:
    """Tests for login request schema."""
    
    def test_login_schema(self):
        """Test login request schema."""
        from services.api_gateway.routes.auth import LoginRequest
        
        request = LoginRequest(
            email="test@example.com",
            password="password123",
        )
        
        assert request.email == "test@example.com"
