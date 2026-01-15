"""
Session Management.

Manages user sessions with JWT token support.
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from shared.logging import get_logger


logger = get_logger(__name__)


@dataclass
class Session:
    """User session."""
    session_id: str
    user_id: str
    tenant_id: str = "default"
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=24))
    last_activity: datetime = field(default_factory=datetime.utcnow)
    
    device_info: str = ""
    ip_address: str = ""
    
    is_active: bool = True
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
    
    def touch(self):
        """Update last activity."""
        self.last_activity = datetime.utcnow()
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "device_info": self.device_info,
            "is_active": self.is_active,
        }


class SessionManager:
    """
    Manages user sessions.
    
    Supports:
    - In-memory storage (default)
    - Database storage
    """
    
    def __init__(self, session_hours: int = 24):
        self.session_hours = session_hours
        self._sessions: dict[str, Session] = {}
        
    async def create_session(
        self,
        user_id: str,
        tenant_id: str = "default",
        device_info: str = "",
        ip_address: str = "",
    ) -> Session:
        """Create new session."""
        session = Session(
            session_id=f"sess_{uuid4().hex[:16]}",
            user_id=user_id,
            tenant_id=tenant_id,
            expires_at=datetime.utcnow() + timedelta(hours=self.session_hours),
            device_info=device_info,
            ip_address=ip_address,
        )
        
        self._sessions[session.session_id] = session
        logger.debug(f"Created session: {session.session_id}")
        
        return session
    
    async def get_session(self, session_id: str) -> Session | None:
        """Get session by ID."""
        session = self._sessions.get(session_id)
        
        if session and session.is_active:
            if session.is_expired():
                await self.end_session(session_id)
                return None
            session.touch()
            return session
        
        return None
    
    async def refresh_session(self, session_id: str) -> Session | None:
        """Extend session expiration."""
        session = self._sessions.get(session_id)
        
        if session and session.is_active and not session.is_expired():
            session.expires_at = datetime.utcnow() + timedelta(hours=self.session_hours)
            session.touch()
            return session
        
        return None
    
    async def end_session(self, session_id: str):
        """End/invalidate session."""
        if session_id in self._sessions:
            self._sessions[session_id].is_active = False
            logger.debug(f"Ended session: {session_id}")
    
    async def get_user_sessions(self, user_id: str) -> list[Session]:
        """Get all active sessions for user."""
        return [
            s for s in self._sessions.values()
            if s.user_id == user_id and s.is_active and not s.is_expired()
        ]
    
    async def cleanup_expired(self):
        """Remove expired sessions."""
        expired = [
            sid for sid, s in self._sessions.items()
            if s.is_expired() or not s.is_active
        ]
        for sid in expired:
            del self._sessions[sid]
        
        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired sessions")


# ============================================================================
# JWT Token Support
# ============================================================================

class JWTManager:
    """
    Manages JWT tokens for stateless authentication.
    
    Uses:
    - Access Token: Short-lived (15min - 1hr)
    - Refresh Token: Long-lived (7 days)
    """
    
    def __init__(
        self,
        secret_key: str = None,
        access_token_minutes: int = 60,
        refresh_token_days: int = 7,
    ):
        self.secret_key = secret_key or os.getenv("JWT_SECRET", secrets.token_hex(32))
        self.access_token_minutes = access_token_minutes
        self.refresh_token_days = refresh_token_days
        self.algorithm = "HS256"
    
    def create_access_token(
        self,
        user_id: str,
        tenant_id: str = "default",
        role: str = "user",
        extra_claims: dict = None,
    ) -> str:
        """Create access token."""
        try:
            import jwt
            
            payload = {
                "sub": user_id,
                "tenant_id": tenant_id,
                "role": role,
                "type": "access",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=self.access_token_minutes),
            }
            
            if extra_claims:
                payload.update(extra_claims)
            
            return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
        except ImportError:
            # Fallback: simple base64 token (not secure)
            import base64
            import json
            
            payload = {
                "sub": user_id,
                "exp": (datetime.utcnow() + timedelta(minutes=self.access_token_minutes)).timestamp(),
            }
            return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create refresh token."""
        try:
            import jwt
            
            payload = {
                "sub": user_id,
                "type": "refresh",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(days=self.refresh_token_days),
            }
            
            return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
        except ImportError:
            return secrets.token_urlsafe(32)
    
    def verify_token(self, token: str) -> dict | None:
        """Verify and decode token."""
        try:
            import jwt
            
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
            
        except ImportError:
            # Fallback
            import base64
            import json
            
            try:
                payload = json.loads(base64.urlsafe_b64decode(token).decode())
                if payload.get("exp", 0) < datetime.utcnow().timestamp():
                    return None
                return payload
            except:
                return None
                
        except Exception:
            return None
    
    def create_tokens(
        self,
        user_id: str,
        tenant_id: str = "default",
        role: str = "user",
    ) -> dict:
        """Create both access and refresh tokens."""
        return {
            "access_token": self.create_access_token(user_id, tenant_id, role),
            "refresh_token": self.create_refresh_token(user_id),
            "token_type": "bearer",
            "expires_in": self.access_token_minutes * 60,
        }


# ============================================================================
# Singleton
# ============================================================================

_session_manager: SessionManager | None = None
_jwt_manager: JWTManager | None = None


def get_session_manager() -> SessionManager:
    """Get singleton session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def get_jwt_manager() -> JWTManager:
    """Get singleton JWT manager."""
    global _jwt_manager
    if _jwt_manager is None:
        _jwt_manager = JWTManager()
    return _jwt_manager
