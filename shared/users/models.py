"""
User Management Models.

Defines User, UserRole, and APIKey for multi-user support.
PostgreSQL-ready with tenant isolation preparation.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class UserRole(Enum):
    """User roles for access control."""
    ADMIN = "admin"         # Full system access
    USER = "user"           # Standard user
    VIEWER = "viewer"       # Read-only access
    SERVICE = "service"     # Service-to-service
    ANONYMOUS = "anonymous" # Unauthenticated (backward compat)


@dataclass
class User:
    """
    User model.
    
    Supports tenant isolation preparation via tenant_id field.
    When tenant isolation is disabled, all users share tenant_id="default".
    """
    user_id: str
    email: str
    name: str
    role: UserRole = UserRole.USER
    tenant_id: str = "default"      # For future multi-tenant
    
    # Security
    password_hash: str = ""         # bcrypt hash
    email_verified: bool = False
    is_active: bool = True
    
    # Settings
    settings: dict = field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_login_at: datetime | None = None
    
    @classmethod
    def create(
        cls,
        email: str,
        name: str,
        password: str = "",
        role: UserRole = UserRole.USER,
        tenant_id: str = "default",
    ) -> User:
        """Create new user with hashed password."""
        user = cls(
            user_id=f"user_{uuid4().hex[:12]}",
            email=email.lower().strip(),
            name=name.strip(),
            role=role,
            tenant_id=tenant_id,
        )
        if password:
            user.set_password(password)
        return user
    
    @classmethod
    def anonymous(cls) -> User:
        """Create anonymous user for backward compatibility."""
        return cls(
            user_id="anonymous",
            email="",
            name="Anonymous",
            role=UserRole.ANONYMOUS,
            tenant_id="default",
        )
    
    def set_password(self, password: str):
        """Hash and set password."""
        # Use bcrypt in production, fallback to sha256 for simplicity
        try:
            import bcrypt
            self.password_hash = bcrypt.hashpw(
                password.encode(), bcrypt.gensalt()
            ).decode()
        except ImportError:
            # Fallback (not secure for production)
            salt = secrets.token_hex(16)
            hash_val = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
            self.password_hash = f"sha256:{salt}:{hash_val}"
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash."""
        if not self.password_hash:
            return False
        
        try:
            import bcrypt
            return bcrypt.checkpw(
                password.encode(),
                self.password_hash.encode()
            )
        except ImportError:
            # Fallback
            if self.password_hash.startswith("sha256:"):
                _, salt, stored_hash = self.password_hash.split(":", 2)
                check_hash = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
                return check_hash == stored_hash
            return False
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert to dictionary."""
        data = {
            "user_id": self.user_id,
            "email": self.email,
            "name": self.name,
            "role": self.role.value,
            "tenant_id": self.tenant_id,
            "is_active": self.is_active,
            "email_verified": self.email_verified,
            "settings": self.settings,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if self.last_login_at:
            data["last_login_at"] = self.last_login_at.isoformat()
        if include_sensitive:
            data["password_hash"] = self.password_hash
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> User:
        """Create from dictionary."""
        return cls(
            user_id=data["user_id"],
            email=data["email"],
            name=data["name"],
            role=UserRole(data.get("role", "user")),
            tenant_id=data.get("tenant_id", "default"),
            password_hash=data.get("password_hash", ""),
            email_verified=data.get("email_verified", False),
            is_active=data.get("is_active", True),
            settings=data.get("settings", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.utcnow(),
            last_login_at=datetime.fromisoformat(data["last_login_at"]) if data.get("last_login_at") else None,
        )


@dataclass  
class APIKey:
    """
    API Key for programmatic access.
    
    Keys are prefixed with "kea_" for identification.
    The raw key is only returned once at creation - only hash is stored.
    """
    key_id: str
    user_id: str
    name: str
    key_hash: str               # SHA-256 hash of the raw key
    key_prefix: str             # First 8 chars for identification
    
    scopes: list[str] = field(default_factory=lambda: ["read", "write"])
    rate_limit: int = 1000      # Requests per hour
    
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    
    @classmethod
    def create(
        cls,
        user_id: str,
        name: str,
        scopes: list[str] = None,
        rate_limit: int = 1000,
        expires_at: datetime = None,
    ) -> tuple["APIKey", str]:
        """
        Create new API key.
        
        Returns:
            (APIKey, raw_key) - raw_key is only available at creation
        """
        raw_key = f"kea_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        api_key = cls(
            key_id=f"key_{uuid4().hex[:12]}",
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            key_prefix=raw_key[:12],
            scopes=scopes or ["read", "write"],
            rate_limit=rate_limit,
            expires_at=expires_at,
        )
        
        return api_key, raw_key
    
    @classmethod
    def verify(cls, raw_key: str, stored_hash: str) -> bool:
        """Verify raw key against stored hash."""
        if not raw_key.startswith("kea_"):
            return False
        check_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        return secrets.compare_digest(check_hash, stored_hash)
    
    def is_expired(self) -> bool:
        """Check if key is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def has_scope(self, scope: str) -> bool:
        """Check if key has required scope."""
        return scope in self.scopes or "admin" in self.scopes
    
    def to_dict(self) -> dict:
        """Convert to dictionary (without hash)."""
        return {
            "key_id": self.key_id,
            "user_id": self.user_id,
            "name": self.name,
            "key_prefix": self.key_prefix,
            "scopes": self.scopes,
            "rate_limit": self.rate_limit,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }


# ============================================================================
# SQL Schema (for PostgreSQL migration)
# ============================================================================

USERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(50) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    tenant_id VARCHAR(50) DEFAULT 'default',
    password_hash TEXT,
    email_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_tenant ON users(tenant_id);
"""

API_KEYS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS api_keys (
    key_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(64) NOT NULL,
    key_prefix VARCHAR(12) NOT NULL,
    scopes TEXT[] DEFAULT ARRAY['read', 'write'],
    rate_limit INTEGER DEFAULT 1000,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON api_keys(key_prefix);
"""
