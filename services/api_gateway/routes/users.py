"""
User Routes.

Endpoints for user profile and API key management.
"""

from __future__ import annotations

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from shared.logging.main import get_logger
from shared.users import User, UserRole
from shared.users.manager import get_user_manager, get_api_key_manager
from services.api_gateway.middleware.auth import get_current_user_required, require_role
from shared.config import get_settings


logger = get_logger(__name__)
router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class UpdateProfileRequest(BaseModel):
    """Update profile request."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    settings: Optional[dict] = None


class CreateAPIKeyRequest(BaseModel):
    """Create API key request."""
    name: str = Field(..., min_length=1, max_length=255)
    scopes: Optional[List[str]] = None
    rate_limit: Optional[int] = Field(None, ge=1, le=get_settings().auth.api_key_max_rate_limit)


class APIKeyResponse(BaseModel):
    """API key response (without raw key)."""
    key_id: str
    name: str
    key_prefix: str
    scopes: List[str]
    rate_limit: int
    is_active: bool
    created_at: str
    expires_at: Optional[str] = None
    last_used_at: Optional[str] = None


class APIKeyCreatedResponse(BaseModel):
    """API key created response (includes raw key ONCE)."""
    key: APIKeyResponse
    raw_key: str  # Only shown once at creation


class UserResponse(BaseModel):
    """User profile response."""
    user_id: str
    email: str
    name: str
    role: str
    tenant_id: str
    is_active: bool
    created_at: str


# ============================================================================
# Routes
# ============================================================================

@router.get("/me", response_model=UserResponse)
async def get_profile(user: User = Depends(get_current_user_required)):
    """Get current user profile."""
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        tenant_id=user.tenant_id,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
    )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    request: UpdateProfileRequest,
    user: User = Depends(get_current_user_required),
):
    """Update current user profile."""
    user_manager = await get_user_manager()
    
    updates = {}
    if request.name is not None:
        updates["name"] = request.name
    if request.settings is not None:
        # Merge with existing settings
        new_settings = {**user.settings, **request.settings}
        updates["settings"] = str(new_settings)
    
    if updates:
        await user_manager.update_user(user.user_id, **updates)
        user = await user_manager.get_user(user.user_id)
    
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        tenant_id=user.tenant_id,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
    )


@router.get("/me/keys", response_model=List[APIKeyResponse])
async def list_api_keys(user: User = Depends(get_current_user_required)):
    """List user's API keys."""
    key_manager = await get_api_key_manager()
    
    keys = await key_manager.list_keys(user.user_id)
    
    return [
        APIKeyResponse(
            key_id=k.key_id,
            name=k.name,
            key_prefix=k.key_prefix,
            scopes=k.scopes,
            rate_limit=k.rate_limit,
            is_active=k.is_active,
            created_at=k.created_at.isoformat(),
            expires_at=k.expires_at.isoformat() if k.expires_at else None,
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
        )
        for k in keys
    ]


@router.post("/me/keys", response_model=APIKeyCreatedResponse)
async def create_api_key(
    request: CreateAPIKeyRequest,
    user: User = Depends(get_current_user_required),
):
    """
    Create new API key.
    
    **Important**: The raw key is only shown once. Store it safely.
    """
    key_manager = await get_api_key_manager()
    
    api_key, raw_key = await key_manager.create_key(
        user_id=user.user_id,
        name=request.name,
        scopes=request.scopes,
        rate_limit=request.rate_limit or get_settings().auth.api_key_default_rate_limit,
    )
    
    logger.info(f"Created API key for user {user.user_id}: {api_key.key_prefix}...")
    
    return APIKeyCreatedResponse(
        key=APIKeyResponse(
            key_id=api_key.key_id,
            name=api_key.name,
            key_prefix=api_key.key_prefix,
            scopes=api_key.scopes,
            rate_limit=api_key.rate_limit,
            is_active=api_key.is_active,
            created_at=api_key.created_at.isoformat(),
            expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
            last_used_at=None,
        ),
        raw_key=raw_key,
    )


@router.delete("/me/keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    user: User = Depends(get_current_user_required),
):
    """Revoke API key."""
    key_manager = await get_api_key_manager()
    
    await key_manager.revoke_key(key_id, user_id=user.user_id)
    
    logger.info(f"Revoked API key {key_id} for user {user.user_id}")
    
    return {"message": "API key revoked"}


# ============================================================================
# Admin Routes
# ============================================================================

@router.get(
    "",
    response_model=List[UserResponse],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def list_users(
    limit: int = Query(get_settings().users.default_list_limit, ge=1, le=get_settings().users.max_list_limit),
    offset: int = 0,
):
    """List all users (admin only)."""
    user_manager = await get_user_manager()
    
    users = await user_manager.list_users(limit=limit, offset=offset)
    
    return [
        UserResponse(
            user_id=u.user_id,
            email=u.email,
            name=u.name,
            role=u.role.value,
            tenant_id=u.tenant_id,
            is_active=u.is_active,
            created_at=u.created_at.isoformat(),
        )
        for u in users
    ]
