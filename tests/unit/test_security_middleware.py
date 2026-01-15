"""
Unit Tests: Security Middleware.

Tests for security headers and input sanitization.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from services.api_gateway.middleware.security import (
    SecurityHeadersMiddleware,
    InputSanitizer,
    RequestValidationMiddleware,
    get_cors_origins,
)


class TestInputSanitizer:
    """Test input sanitization."""
    
    # SQL Injection Tests
    def test_detects_sql_select(self):
        """Test SQL SELECT detection."""
        assert InputSanitizer.check_sql_injection("SELECT * FROM users") is True
    
    def test_detects_sql_union(self):
        """Test SQL UNION detection."""
        assert InputSanitizer.check_sql_injection("1 UNION SELECT password FROM users") is True
    
    def test_detects_sql_comment(self):
        """Test SQL comment detection."""
        assert InputSanitizer.check_sql_injection("admin'--") is True
    
    def test_detects_sql_or_1_equals_1(self):
        """Test classic SQL injection."""
        assert InputSanitizer.check_sql_injection("' OR 1=1") is True
    
    def test_safe_sql_input(self):
        """Test normal input passes."""
        assert InputSanitizer.check_sql_injection("normal search query") is False
        assert InputSanitizer.check_sql_injection("SELECT a book") is False  # Word 'select' in context
    
    # XSS Tests
    def test_detects_script_tag(self):
        """Test script tag detection."""
        assert InputSanitizer.check_xss("<script>alert('xss')</script>") is True
    
    def test_detects_javascript_url(self):
        """Test javascript: URL detection."""
        assert InputSanitizer.check_xss("javascript:alert(1)") is True
    
    def test_detects_onclick(self):
        """Test onclick handler detection."""
        assert InputSanitizer.check_xss('<div onclick="evil()">') is True
    
    def test_detects_iframe(self):
        """Test iframe detection."""
        assert InputSanitizer.check_xss("<iframe src='evil.com'>") is True
    
    def test_safe_xss_input(self):
        """Test normal input passes."""
        assert InputSanitizer.check_xss("Hello <b>world</b>") is False
        assert InputSanitizer.check_xss("Use JavaScript for scripting") is False
    
    # Path Traversal Tests
    def test_detects_dot_dot_slash(self):
        """Test ../ detection."""
        assert InputSanitizer.check_path_traversal("../../../etc/passwd") is True
    
    def test_detects_encoded_traversal(self):
        """Test URL encoded traversal."""
        assert InputSanitizer.check_path_traversal("%2e%2e%2f") is True
    
    def test_safe_path_input(self):
        """Test normal paths pass."""
        assert InputSanitizer.check_path_traversal("/api/v1/users") is False
        assert InputSanitizer.check_path_traversal("folder/file.txt") is False
    
    # Sanitization Tests
    def test_sanitize_html_entities(self):
        """Test HTML entity escaping."""
        result = InputSanitizer.sanitize_string("<script>")
        
        assert "<" not in result
        assert ">" not in result
        assert "&lt;" in result
        assert "&gt;" in result
    
    def test_sanitize_quotes(self):
        """Test quote escaping."""
        result = InputSanitizer.sanitize_string('test"value\'here')
        
        assert '"' not in result
        assert "'" not in result
    
    # Combined Safety Check
    def test_is_safe_input_clean(self):
        """Test clean input passes all checks."""
        is_safe, reason = InputSanitizer.is_safe_input("Hello world")
        
        assert is_safe is True
        assert reason == ""
    
    def test_is_safe_input_sql(self):
        """Test SQL injection fails check."""
        is_safe, reason = InputSanitizer.is_safe_input("SELECT * FROM users")
        
        assert is_safe is False
        assert "SQL" in reason
    
    def test_is_safe_input_xss(self):
        """Test XSS fails check."""
        is_safe, reason = InputSanitizer.is_safe_input("<script>alert(1)</script>")
        
        assert is_safe is False
        assert "XSS" in reason


class TestSecurityHeadersMiddleware:
    """Test security headers."""
    
    @pytest.mark.asyncio
    async def test_adds_basic_headers(self):
        """Test basic security headers are added."""
        app = MagicMock()
        middleware = SecurityHeadersMiddleware(app)
        
        request = MagicMock()
        response = MagicMock()
        response.headers = {}
        
        async def mock_call_next(req):
            return response
        
        result = await middleware.dispatch(request, mock_call_next)
        
        assert result.headers["X-Content-Type-Options"] == "nosniff"
        assert result.headers["X-Frame-Options"] == "DENY"
        assert result.headers["X-XSS-Protection"] == "1; mode=block"


class TestCORSOrigins:
    """Test CORS origin configuration."""
    
    def test_development_allows_all(self):
        """Test development mode allows all origins."""
        from unittest.mock import patch
        
        with patch("services.api_gateway.middleware.security.get_environment_config") as mock:
            mock.return_value.is_development = True
            
            origins = get_cors_origins()
            
            assert origins == ["*"]
    
    def test_production_uses_env_var(self):
        """Test production uses CORS_ORIGINS env var."""
        import os
        from unittest.mock import patch
        
        with patch("services.api_gateway.middleware.security.get_environment_config") as mock_config:
            mock_config.return_value.is_development = False
            
            with patch.dict(os.environ, {"CORS_ORIGINS": "https://example.com,https://app.example.com"}):
                origins = get_cors_origins()
                
                assert "https://example.com" in origins
                assert "https://app.example.com" in origins
