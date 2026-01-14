"""
Tests for Resource Guards.
"""

import pytest


class TestRateLimiter:
    """Tests for RateLimiter."""
    
    def test_create_rate_limiter(self):
        """Test rate limiter creation."""
        from services.orchestrator.core.guards import RateLimiter
        
        limiter = RateLimiter(max_per_minute=10)
        
        assert limiter.max_per_minute == 10
        print("\n✅ RateLimiter created")
    
    def test_check_allows_initial(self):
        """Test initial requests are allowed."""
        from services.orchestrator.core.guards import RateLimiter
        
        limiter = RateLimiter(max_per_minute=5)
        
        # First 5 should pass
        for i in range(5):
            assert limiter.check("test_key") is True
        
        print("\n✅ Initial requests allowed")
    
    def test_check_blocks_over_limit(self):
        """Test requests over limit are blocked."""
        from services.orchestrator.core.guards import RateLimiter
        
        limiter = RateLimiter(max_per_minute=3)
        
        # Use up quota
        for _ in range(3):
            limiter.check("over_limit")
        
        # 4th should fail
        assert limiter.check("over_limit") is False
        
        print("\n✅ Over-limit requests blocked")
    
    def test_check_separate_keys(self):
        """Test different keys have separate quotas."""
        from services.orchestrator.core.guards import RateLimiter
        
        limiter = RateLimiter(max_per_minute=2)
        
        # Use up quota for key A
        limiter.check("key_a")
        limiter.check("key_a")
        assert limiter.check("key_a") is False
        
        # Key B should still work
        assert limiter.check("key_b") is True
        
        print("\n✅ Separate keys have separate quotas")
    
    def test_get_remaining(self):
        """Test getting remaining quota."""
        from services.orchestrator.core.guards import RateLimiter
        
        limiter = RateLimiter(max_per_minute=10)
        
        assert limiter.get_remaining("fresh_key") == 10
        
        limiter.check("fresh_key")
        limiter.check("fresh_key")
        
        assert limiter.get_remaining("fresh_key") == 8
        
        print("\n✅ Remaining quota tracking works")


class TestResourceGuard:
    """Tests for ResourceGuard."""
    
    def test_create_guard(self):
        """Test resource guard creation."""
        from services.orchestrator.core.guards import ResourceGuard
        
        guard = ResourceGuard(
            max_agents_per_minute=100,
            max_memory_percent=85.0,
            max_tool_calls_per_minute=100,
        )
        
        assert guard.max_agents_per_minute == 100
        assert guard.max_memory_percent == 85.0
        
        print("\n✅ ResourceGuard created")
    
    @pytest.mark.asyncio
    async def test_check_can_spawn(self):
        """Test spawn permission check."""
        from services.orchestrator.core.guards import ResourceGuard
        
        guard = ResourceGuard(max_agents_per_minute=5)
        
        # Should allow initial spawns
        can_spawn = await guard.check_can_spawn("session_1")
        assert can_spawn is True
        
        print("\n✅ Spawn permission check works")
    
    @pytest.mark.asyncio
    async def test_check_memory_ok(self):
        """Test memory check."""
        from services.orchestrator.core.guards import ResourceGuard
        
        guard = ResourceGuard(max_memory_percent=99.0)  # Very high threshold
        
        # Should pass with high threshold
        memory_ok = await guard.check_memory_ok()
        assert memory_ok is True
        
        print("\n✅ Memory check works")
    
    def test_check_tool_quota(self):
        """Test tool call quota."""
        from services.orchestrator.core.guards import ResourceGuard
        
        guard = ResourceGuard(max_tool_calls_per_minute=3)
        
        # Use up quota
        assert guard.check_tool_quota("scraper") is True
        assert guard.check_tool_quota("scraper") is True
        assert guard.check_tool_quota("scraper") is True
        assert guard.check_tool_quota("scraper") is False
        
        print("\n✅ Tool quota enforcement works")
    
    def test_register_agent_spawn(self):
        """Test agent spawn tracking."""
        from services.orchestrator.core.guards import ResourceGuard
        
        guard = ResourceGuard()
        
        assert guard.active_agent_count == 0
        
        guard.register_agent_spawn()
        guard.register_agent_spawn()
        
        assert guard.active_agent_count == 2
        
        guard.register_agent_complete()
        
        assert guard.active_agent_count == 1
        
        print("\n✅ Agent tracking works")
    
    def test_singleton(self):
        """Test resource guard singleton."""
        from services.orchestrator.core.guards import get_resource_guard
        
        g1 = get_resource_guard()
        g2 = get_resource_guard()
        
        assert g1 is g2
        
        print("\n✅ Singleton works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
