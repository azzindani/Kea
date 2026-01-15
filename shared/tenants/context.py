"""
Tenant Context.

Provides tenant isolation for multi-tenant deployments.
Currently user-only isolation, but prepared for full tenant isolation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shared.logging import get_logger


logger = get_logger(__name__)


@dataclass
class TenantContext:
    """
    Tenant isolation context.
    
    Currently:
    - All users share tenant_id="default"
    - Resources filtered by user_id
    
    Future (full tenant isolation):
    - Each tenant has separate data
    - Resources prefixed/filtered by tenant_id
    - Separate resource quotas per tenant
    
    Usage:
        context = TenantContext(tenant_id="acme_corp", user_id="user_123")
        
        # Get prefixed cache key
        cache_key = context.cache_key("facts:tesla")
        # → "tenant:acme_corp:facts:tesla"
        
        # Get audit filter
        filter = context.audit_filter()
        # → {"tenant_id": "acme_corp", "user_id": "user_123"}
    """
    
    tenant_id: str = "default"
    user_id: str = ""
    
    # Feature flags for tenant isolation
    enable_tenant_isolation: bool = False  # When True, enforce full isolation
    
    def cache_key(self, key: str) -> str:
        """
        Get cache key with tenant/user prefix.
        
        With tenant isolation: tenant:{tenant_id}:{key}
        Without: user:{user_id}:{key}
        """
        if self.enable_tenant_isolation:
            return f"tenant:{self.tenant_id}:{key}"
        elif self.user_id:
            return f"user:{self.user_id}:{key}"
        return key
    
    def db_filter(self) -> dict:
        """
        Get database filter for queries.
        
        With tenant isolation: {"tenant_id": ...}
        Without: {"user_id": ...}
        """
        if self.enable_tenant_isolation:
            return {"tenant_id": self.tenant_id}
        elif self.user_id:
            return {"user_id": self.user_id}
        return {}
    
    def audit_filter(self) -> dict:
        """Get filter for audit trail queries."""
        filters = {}
        if self.tenant_id and self.tenant_id != "default":
            filters["tenant_id"] = self.tenant_id
        if self.user_id:
            filters["user_id"] = self.user_id
        return filters
    
    def resource_prefix(self) -> str:
        """Get prefix for resource naming (files, etc.)."""
        if self.enable_tenant_isolation:
            return f"{self.tenant_id}/"
        elif self.user_id:
            return f"{self.user_id}/"
        return ""
    
    @classmethod
    def default(cls) -> "TenantContext":
        """Create default context (no isolation)."""
        return cls(tenant_id="default", user_id="")
    
    @classmethod
    def for_user(cls, user_id: str, tenant_id: str = "default") -> "TenantContext":
        """Create context for specific user."""
        return cls(tenant_id=tenant_id, user_id=user_id)


# Singleton for current request context
_current_context: TenantContext | None = None


def get_tenant_context() -> TenantContext:
    """Get current tenant context."""
    global _current_context
    if _current_context is None:
        _current_context = TenantContext.default()
    return _current_context


def set_tenant_context(context: TenantContext):
    """Set current tenant context."""
    global _current_context
    _current_context = context
