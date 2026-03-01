"""
Authentication Middleware.

Provides authentication via:
- API Key (X-API-Key header)
- JWT Token (Authorization: Bearer)
- Session Cookie (web UI)

Falls back to anonymous access for backward compatibility.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, APIKeyHeader

from shared.logging.main import get_logger
from shared.config import get_settings
from shared.users import User, UserRole
from shared.users.manager import get_user_manager, get_api_key_manager
from shared.sessions import get_session_manager, get_jwt_manager
from shared.tenants import TenantContext, set_tenant_context


logger = get_logger(__name__)


# Security schemes initialized below
api_key_header: APIKeyHeader | None = None
bearer_scheme = HTTPBearer(auto_error=False)


def get_api_key_header() -> APIKeyHeader:
    """Lazy initialize API key header from settings."""
    global api_key_header
    if api_key_header is None:
        settings = get_settings()
        api_key_header = APIKeyHeader(
            name=settings.auth.api_key_header_name,
            auto_error=False
        )
    return api_key_header


class AuthMiddleware:
    """
    Authentication middleware.
    
    Authenticates requests via:
    1. API Key (X-API-Key header)
    2. JWT Token (Authorization: Bearer)
    3. Session ID (Cookie)
    4. Anonymous (fallback)
    """
    
    def __init__(self, allow_anonymous: bool | None = None):
        settings = get_settings()
        self.allow_anonymous = allow_anonymous if allow_anonymous is not None else settings.auth.allow_anonymous
    
    async def __call__(self, request: Request, call_next):
        """Process request authentication."""
        
        # Try authentication methods in order
        user = None
        auth_method = None
        
        # 1. API Key
        settings = get_settings()
        api_key = request.headers.get(settings.auth.api_key_header_name)
        if api_key:
            user = await self._auth_api_key(api_key)
            auth_method = "api_key"
        
        # 2. JWT Token
        if not user:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
                user = await self._auth_jwt(token)
                auth_method = "jwt"
        
        # 3. Session Cookie
        if not user:
            session_id = request.cookies.get("session_id")
            if session_id:
                user = await self._auth_session(session_id)
                auth_method = "session"
        
        # 4. Anonymous fallback
        if not user and self.allow_anonymous:
            user = User.anonymous()
            auth_method = "anonymous"
        
        # Set user on request state
        request.state.user = user
        request.state.auth_method = auth_method
        
        # Set tenant context
        if user:
            set_tenant_context(TenantContext.for_user(user.user_id, user.tenant_id))
        
        response = await call_next(request)
        return response
    
    async def _auth_api_key(self, raw_key: str) -> User | None:
        """Authenticate via API key."""
        try:
            key_manager = await get_api_key_manager()
            api_key = await key_manager.validate_key(raw_key)
            
            if api_key:
                user_manager = await get_user_manager()
                return await user_manager.get_user(api_key.user_id)
        except Exception as e:
            logger.warning(f"API key auth failed: {e}")
        
        return None
    
    async def _auth_jwt(self, token: str) -> User | None:
        """Authenticate via JWT token."""
        try:
            jwt_manager = get_jwt_manager()
            payload = jwt_manager.verify_token(token)
            
            if payload and payload.get("type") == "access":
                user_id = payload.get("sub")
                if user_id:
                    user_manager = await get_user_manager()
                    return await user_manager.get_user(user_id)
        except Exception as e:
            logger.warning(f"JWT auth failed: {e}")
        
        return None
    
    async def _auth_session(self, session_id: str) -> User | None:
        """Authenticate via session."""
        try:
            session_manager = get_session_manager()
            session = await session_manager.get_session(session_id)
            
            if session:
                user_manager = await get_user_manager()
                return await user_manager.get_user(session.user_id)
        except Exception as e:
            logger.warning(f"Session auth failed: {e}")
        
        return None


# ============================================================================
# FastAPI Dependencies
# ============================================================================

async def get_current_user(request: Request) -> User:
    """
    Get current authenticated user.
    
    Usage:
        @app.get("/me")
        async def get_me(user: User = Depends(get_current_user)):
            return user.to_dict()
    """
    user = getattr(request.state, "user", None)
    
    if user is None:
        # Try to authenticate
        settings = get_settings()
        api_key = request.headers.get(settings.auth.api_key_header_name)
        if api_key:
            key_manager = await get_api_key_manager()
            key = await key_manager.validate_key(api_key)
            if key:
                user_manager = await get_user_manager()
                user = await user_manager.get_user(key.user_id)
        
        if user is None:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                jwt_manager = get_jwt_manager()
                payload = jwt_manager.verify_token(auth_header[7:])
                if payload:
                    user_manager = await get_user_manager()
                    user = await user_manager.get_user(payload.get("sub"))
    
    if user is None:
        # Allow anonymous for backward compatibility
        user = User.anonymous()
    
    return user


async def get_current_user_required(request: Request) -> User:
    """
    Get current user (required - no anonymous).
    
    Raises 401 if not authenticated.
    """
    user = await get_current_user(request)
    
    if user.role == UserRole.ANONYMOUS:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def require_role(*roles: UserRole):
    """
    Dependency to require specific role(s).
    
    Usage:
        @app.delete("/admin/users/{user_id}")
        async def delete_user(
            user_id: str,
            current_user: User = Depends(require_role(UserRole.ADMIN))
        ):
            ...
    """
    async def check_role(user: User = Depends(get_current_user_required)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"Required role: {', '.join(r.value for r in roles)}",
            )
        return user
    
    return check_role


async def get_optional_user(request: Request) -> User | None:
    """Get current user if authenticated, None otherwise."""
    user = await get_current_user(request)
    if user.role == UserRole.ANONYMOUS:
        return None
    return user


# ============================================================================
# Middleware factory
# ============================================================================

def create_auth_middleware(allow_anonymous: bool = True) -> AuthMiddleware:
    """Create auth middleware instance."""
    return AuthMiddleware(allow_anonymous=allow_anonymous)
