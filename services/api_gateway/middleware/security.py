"""
Security Middleware.

Production security headers and request sanitization.
"""

from __future__ import annotations

import re
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from shared.logging import get_logger
from shared.environment import get_environment_config


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
        
        env_config = get_environment_config()
        
        # Always add these
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Production only
        if env_config.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = "default-src 'self'"
        
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
    
    def __init__(self, app, max_body_size_mb: int = 10):
        super().__init__(app)
        self.max_body_size = max_body_size_mb * 1024 * 1024
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        env_config = get_environment_config()
        
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
        if env_config.is_production:
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
    import os
    
    env_config = get_environment_config()
    
    if env_config.is_development:
        return ["*"]  # Allow all in dev
    
    # Production: whitelist only
    origins = os.getenv("CORS_ORIGINS", "").split(",")
    origins = [o.strip() for o in origins if o.strip()]
    
    if not origins:
        logger.warning("No CORS_ORIGINS configured, defaulting to none")
        return []
    
    return origins
