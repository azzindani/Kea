"""
API Gateway Middleware Package.
"""

from services.api_gateway.middleware.auth import (
    AuthMiddleware,
    get_current_user,
    get_current_user_required,
    get_optional_user,
    require_role,
    create_auth_middleware,
)
from services.api_gateway.middleware.rate_limit import (
    RateLimitMiddleware,
    RateLimitConfig,
)
from services.api_gateway.middleware.security import (
    SecurityHeadersMiddleware,
    RequestValidationMiddleware,
    InputSanitizer,
    get_cors_origins,
)

__all__ = [
    # Auth
    "AuthMiddleware",
    "get_current_user",
    "get_current_user_required",
    "get_optional_user",
    "require_role",
    "create_auth_middleware",
    # Rate Limit
    "RateLimitMiddleware",
    "RateLimitConfig",
    # Security
    "SecurityHeadersMiddleware",
    "RequestValidationMiddleware",
    "InputSanitizer",
    "get_cors_origins",
]

