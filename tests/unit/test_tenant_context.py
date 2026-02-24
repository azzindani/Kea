"""
Unit Tests: Tenant Context.

Tests for multi-tenant isolation.
"""


from shared.tenants.context import (
    TenantContext,
    get_tenant_context,
    set_tenant_context,
)


class TestTenantContext:
    """Test TenantContext dataclass."""

    def test_default_context(self):
        """Test default context creation."""
        context = TenantContext.default()

        assert context.tenant_id == "default"
        assert context.user_id == ""
        assert context.enable_tenant_isolation is False

    def test_for_user(self):
        """Test user context creation."""
        context = TenantContext.for_user("user-123")

        assert context.user_id == "user-123"
        assert context.tenant_id == "default"

    def test_for_user_with_tenant(self):
        """Test user context with specific tenant."""
        context = TenantContext.for_user("user-123", tenant_id="acme_corp")

        assert context.user_id == "user-123"
        assert context.tenant_id == "acme_corp"


class TestCacheKey:
    """Test cache key generation."""

    def test_cache_key_no_user(self):
        """Test cache key without user returns plain key."""
        context = TenantContext(tenant_id="default", user_id="")

        key = context.cache_key("facts:tesla")

        assert key == "facts:tesla"

    def test_cache_key_with_user(self):
        """Test cache key with user prefix."""
        context = TenantContext(tenant_id="default", user_id="user-123")

        key = context.cache_key("facts:tesla")

        assert key == "user:user-123:facts:tesla"

    def test_cache_key_tenant_isolation(self):
        """Test cache key with tenant isolation enabled."""
        context = TenantContext(
            tenant_id="acme_corp",
            user_id="user-123",
            enable_tenant_isolation=True,
        )

        key = context.cache_key("facts:tesla")

        assert key == "tenant:acme_corp:facts:tesla"


class TestDbFilter:
    """Test database filter generation."""

    def test_db_filter_empty(self):
        """Test filter empty when no user."""
        context = TenantContext(tenant_id="default", user_id="")

        filters = context.db_filter()

        assert filters == {}

    def test_db_filter_user(self):
        """Test filter with user_id."""
        context = TenantContext(tenant_id="default", user_id="user-123")

        filters = context.db_filter()

        assert filters == {"user_id": "user-123"}

    def test_db_filter_tenant_isolation(self):
        """Test filter with tenant isolation."""
        context = TenantContext(
            tenant_id="acme_corp",
            user_id="user-123",
            enable_tenant_isolation=True,
        )

        filters = context.db_filter()

        assert filters == {"tenant_id": "acme_corp"}


class TestAuditFilter:
    """Test audit filter generation."""

    def test_audit_filter_empty(self):
        """Test audit filter empty for default tenant."""
        context = TenantContext(tenant_id="default", user_id="")

        filters = context.audit_filter()

        assert filters == {}

    def test_audit_filter_user_only(self):
        """Test audit filter with user only."""
        context = TenantContext(tenant_id="default", user_id="user-123")

        filters = context.audit_filter()

        assert filters == {"user_id": "user-123"}

    def test_audit_filter_tenant_and_user(self):
        """Test audit filter with both tenant and user."""
        context = TenantContext(tenant_id="acme_corp", user_id="user-123")

        filters = context.audit_filter()

        assert filters["tenant_id"] == "acme_corp"
        assert filters["user_id"] == "user-123"


class TestResourcePrefix:
    """Test resource prefix generation."""

    def test_resource_prefix_empty(self):
        """Test empty prefix when no user."""
        context = TenantContext(tenant_id="default", user_id="")

        prefix = context.resource_prefix()

        assert prefix == ""

    def test_resource_prefix_user(self):
        """Test prefix with user."""
        context = TenantContext(tenant_id="default", user_id="user-123")

        prefix = context.resource_prefix()

        assert prefix == "user-123/"

    def test_resource_prefix_tenant(self):
        """Test prefix with tenant isolation."""
        context = TenantContext(
            tenant_id="acme_corp",
            user_id="user-123",
            enable_tenant_isolation=True,
        )

        prefix = context.resource_prefix()

        assert prefix == "acme_corp/"


class TestContextGlobals:
    """Test global context management."""

    def test_get_default_context(self):
        """Test getting default context."""
        # Reset global
        import shared.tenants.context as ctx
        ctx._current_context = None

        context = get_tenant_context()

        assert context.tenant_id == "default"

    def test_set_and_get_context(self):
        """Test setting and getting context."""
        custom_context = TenantContext.for_user("user-456", tenant_id="corp")

        set_tenant_context(custom_context)
        retrieved = get_tenant_context()

        assert retrieved.user_id == "user-456"
        assert retrieved.tenant_id == "corp"
