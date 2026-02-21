"""
Security Middleware.

Production security headers and request sanitization.
"""

from __future__ import annotations

import re
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from shared.logging.main import get_logger
from shared.config import get_settings


logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to responses.
    
    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security (production only)
    - Content-Security-Policy
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        settings = get_settings()
        sec = settings.security
        
        # Always add these
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Production only (or via config)
        if settings.app.environment == "production":
            hsts = f"max-age={sec.hsts_max_age}"
            if sec.hsts_include_subdomains:
                hsts += "; includeSubDomains"
            response.headers["Strict-Transport-Security"] = hsts
            response.headers["Content-Security-Policy"] = sec.csp_policy
        
        return response


class InputSanitizer:
    """
    Input sanitization utilities.
    
    Prevents XSS, SQL injection, and path traversal.
    """
    
    # Patterns for dangerous input
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b)",
        r"(--|\#|\/\*)",
        r"(\bOR\b\s+\d+\s*=\s*\d+)",
        r"(\bAND\b\s+\d+\s*=\s*\d+)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e/",
    ]
    
    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        """Check for SQL injection patterns. Returns True if suspicious."""
        if not isinstance(value, str):
            return False
        
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def check_xss(cls, value: str) -> bool:
        """Check for XSS patterns. Returns True if suspicious."""
        if not isinstance(value, str):
            return False
        
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def check_path_traversal(cls, value: str) -> bool:
        """Check for path traversal. Returns True if suspicious."""
        if not isinstance(value, str):
            return False
        
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def sanitize_string(cls, value: str) -> str:
        """Sanitize string by escaping dangerous characters."""
        if not isinstance(value, str):
            return value
        
        # HTML escape
        escapes = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#x27;",
        }
        
        for char, escape in escapes.items():
            value = value.replace(char, escape)
        
        return value
    
    @classmethod
    def is_safe_input(cls, value: str) -> tuple[bool, str]:
        """
        Check if input is safe.
        
        Returns:
            (is_safe, reason)
        """
        if cls.check_sql_injection(value):
            return False, "Potential SQL injection detected"
        if cls.check_xss(value):
            return False, "Potential XSS detected"
        if cls.check_path_traversal(value):
            return False, "Potential path traversal detected"
        return True, ""


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Validate incoming requests.
    
    - Check request size
    - Check for suspicious patterns
    - Log security events
    """
    
    def __init__(self, app, max_body_size_mb: int | None = None):
        super().__init__(app)
        settings = get_settings()
        limit = max_body_size_mb or settings.security.max_body_size_mb
        self.max_body_size = limit * 1024 * 1024
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        settings = get_settings()
        
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_body_size:
                    logger.warning(f"Request too large: {content_length} bytes")
                    return Response(
                        content='{"detail": "Request too large"}',
                        status_code=413,
                        media_type="application/json",
                    )
            except ValueError:
                pass
        
        # Check query parameters in production
        if settings.app.environment == "production":
            for key, value in request.query_params.items():
                is_safe, reason = InputSanitizer.is_safe_input(value)
                if not is_safe:
                    logger.warning(f"Suspicious query param {key}: {reason}")
                    return Response(
                        content='{"detail": "Invalid input"}',
                        status_code=400,
                        media_type="application/json",
                    )
        
        return await call_next(request)


# CORS configuration for production
def get_cors_origins() -> list[str]:
    """Get allowed CORS origins based on environment."""
    from shared.config import get_settings
    settings = get_settings()
    
    # Development: Allow all (unless specific origins provided)
    if settings.app.environment == "development" and settings.security.cors_origins == ["*"]:
        return ["*"]
        
    return settings.security.cors_origins
