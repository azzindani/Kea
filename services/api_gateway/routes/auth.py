"""
Authentication Routes.

Endpoints for login, logout, token refresh.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from pydantic import BaseModel, EmailStr, Field

from shared.logging.main import get_logger
from shared.users import User
from shared.users.manager import get_user_manager
from shared.sessions import get_session_manager, get_jwt_manager
from services.api_gateway.middleware.auth import get_current_user_required
from shared.config import get_settings


logger = get_logger(__name__)
router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class LoginRequest(BaseModel):
    """Login request."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    """Registration request."""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=get_settings().auth.password_min_length)


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str


# ============================================================================
# Routes
# ============================================================================

@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """
    Register new user.
    
    Returns access and refresh tokens.
    """
    user_manager = await get_user_manager()
    
    # Check if email exists
    existing = await user_manager.get_by_email(request.email)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )
    
    # Create user
    user = await user_manager.create_user(
        email=request.email,
        name=request.name,
        password=request.password,
    )
    
    # Generate tokens
    jwt_manager = get_jwt_manager()
    tokens = jwt_manager.create_tokens(
        user_id=user.user_id,
        tenant_id=user.tenant_id,
        role=user.role.value,
    )
    
    logger.info(f"User registered: {user.email}")
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"],
        user=user.to_dict(),
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, response: Response):
    """
    Login with email and password.
    
    Returns access and refresh tokens.
    Also sets session cookie for web UI.
    """
    user_manager = await get_user_manager()
    
    user = await user_manager.authenticate_email(request.email, request.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is deactivated",
        )
    
    # Generate tokens
    jwt_manager = get_jwt_manager()
    tokens = jwt_manager.create_tokens(
        user_id=user.user_id,
        tenant_id=user.tenant_id,
        role=user.role.value,
    )
    
    # Create session for cookie-based auth
    session_manager = get_session_manager()
    session = await session_manager.create_session(
        user_id=user.user_id,
        tenant_id=user.tenant_id,
    )
    
    # Set session cookie
    settings = get_settings()
    
    response.set_cookie(
        key="session_id",
        value=session.session_id,
        httponly=True,
        max_age=settings.auth.session_hours * 3600,
        samesite="lax",
    )
    
    logger.info(f"User logged in: {user.email}")
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"],
        user=user.to_dict(),
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user_required),
):
    """
    Logout user.
    
    Invalidates session and clears cookie.
    """
    # End session
    session_id = request.cookies.get("session_id")
    if session_id:
        session_manager = get_session_manager()
        await session_manager.end_session(session_id)
    
    # Clear cookie
    response.delete_cookie("session_id")
    
    logger.info(f"User logged out: {user.email}")
    
    return MessageResponse(message="Logged out successfully")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest):
    """
    Refresh access token.
    
    Exchange refresh token for new access token.
    """
    jwt_manager = get_jwt_manager()
    
    payload = jwt_manager.verify_token(request.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token",
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload",
        )
    
    user_manager = await get_user_manager()
    user = await user_manager.get_user(user_id)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="User not found or inactive",
        )
    
    # Generate new tokens
    tokens = jwt_manager.create_tokens(
        user_id=user.user_id,
        tenant_id=user.tenant_id,
        role=user.role.value,
    )
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"],
        user=user.to_dict(),
    )


@router.get("/me")
async def get_me(user: User = Depends(get_current_user_required)):
    """Get current user profile."""
    return user.to_dict()
