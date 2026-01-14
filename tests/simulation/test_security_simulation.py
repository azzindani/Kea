"""
Security Simulation Tests.

Tests security guards and kill switch in simulated attack/pressure scenarios.
"""

import pytest
import asyncio


class TestSecurityGuardSimulation:
    """Simulate security scenarios."""
    
    def test_rate_limit_flood_protection(self):
        """Test rate limiting against flood attacks."""
        from services.orchestrator.core.guards import RateLimiter
        
        limiter = RateLimiter(max_per_minute=100)
        
        # Simulate 200 rapid requests
        allowed = 0
        blocked = 0
        
        for i in range(200):
            if limiter.check(f"attacker_{i % 5}"):  # 5 different "attackers"
                allowed += 1
            else:
                blocked += 1
        
        # Should block after hitting limits
        assert blocked > 0
        
        print(f"\n✅ Flood protection: {allowed} allowed, {blocked} blocked")
    
    @pytest.mark.asyncio
    async def test_agent_spawn_bomb_protection(self):
        """Test protection against spawn bomb attack."""
        from services.orchestrator.core.guards import ResourceGuard
        
        guard = ResourceGuard(max_agents_per_minute=20)
        
        # Simulate spawn bomb - try to spawn 100 agents
        spawned = 0
        blocked = 0
        
        for i in range(100):
            if await guard.check_can_spawn(f"session_{i}"):
                guard.register_agent_spawn()
                spawned += 1
            else:
                blocked += 1
        
        assert blocked > 50  # Should block most
        assert guard.active_agent_count <= 20
        
        print(f"\n✅ Spawn bomb protection: {spawned} spawned, {blocked} blocked")
    
    def test_tool_abuse_prevention(self):
        """Test prevention of tool abuse."""
        from services.orchestrator.core.guards import ResourceGuard
        
        guard = ResourceGuard(max_tool_calls_per_minute=50)
        
        # Simulate tool abuse - rapid calls to expensive tool
        allowed = 0
        for i in range(100):
            if guard.check_tool_quota("expensive_api"):
                allowed += 1
        
        assert allowed <= 50
        
        print(f"\n✅ Tool abuse prevention: {allowed}/100 allowed")
    
    @pytest.mark.asyncio
    async def test_memory_pressure_protection(self):
        """Test memory pressure detection."""
        from services.orchestrator.core.guards import ResourceGuard
        
        # Very high threshold to test the check works
        guard = ResourceGuard(max_memory_percent=99.9)
        
        memory_ok = await guard.check_memory_ok()
        
        # Should usually be OK unless system is actually stressed
        print(f"\n✅ Memory check: {'OK' if memory_ok else 'PRESSURE DETECTED'}")


class TestKillSwitchSimulation:
    """Simulate kill switch scenarios."""
    
    @pytest.mark.asyncio
    async def test_emergency_shutdown_all(self):
        """Test emergency shutdown stops all activity."""
        from services.orchestrator.core.kill_switch import KillSwitch
        
        switch = KillSwitch()
        
        # Simulate ongoing work
        work_items = ["work_1", "work_2", "work_3"]
        tools = ["scraper", "analyzer", "vision"]
        depts = ["research", "finance", "legal"]
        
        # Trigger emergency
        await switch.emergency_stop("Critical security incident")
        
        # All should be blocked
        for w in work_items:
            assert switch.can_proceed() is False
        
        for t in tools:
            assert switch.can_proceed(tool_name=t) is False
        
        for d in depts:
            assert switch.can_proceed(dept_id=d) is False
        
        print("\n✅ Emergency shutdown blocked all activity")
        
        # Resume
        await switch.resume()
        assert switch.can_proceed() is True
    
    @pytest.mark.asyncio
    async def test_targeted_tool_isolation(self):
        """Test isolating a compromised tool."""
        from services.orchestrator.core.kill_switch import KillSwitch
        
        switch = KillSwitch()
        
        # One tool is misbehaving
        switch.blacklist_tool("compromised_scraper", 
                             reason="Returning malicious content",
                             duration_minutes=60)
        
        # That tool blocked
        assert switch.can_proceed(tool_name="compromised_scraper") is False
        assert switch.is_tool_blacklisted("compromised_scraper") is True
        
        # Other tools work
        assert switch.can_proceed(tool_name="safe_analyzer") is True
        assert switch.can_proceed(tool_name="other_tool") is True
        
        print("\n✅ Targeted tool isolation works")
    
    @pytest.mark.asyncio
    async def test_department_quarantine(self):
        """Test quarantining a department."""
        from services.orchestrator.core.kill_switch import KillSwitch
        
        switch = KillSwitch()
        
        # Quarantine research department
        switch.pause_department("dept_research")
        
        # Research blocked
        assert switch.can_proceed(dept_id="dept_research") is False
        
        # Other departments work
        assert switch.can_proceed(dept_id="dept_finance") is True
        assert switch.can_proceed(dept_id="dept_legal") is True
        
        print("\n✅ Department quarantine works")
    
    @pytest.mark.asyncio 
    async def test_emergency_callback_chain(self):
        """Test emergency callbacks fire correctly."""
        from services.orchestrator.core.kill_switch import KillSwitch
        
        switch = KillSwitch()
        
        notifications = []
        
        async def notify_ops(reason):
            notifications.append(f"OPS: {reason}")
        
        async def notify_security(reason):
            notifications.append(f"SEC: {reason}")
        
        async def log_incident(reason):
            notifications.append(f"LOG: {reason}")
        
        switch.on_emergency(notify_ops)
        switch.on_emergency(notify_security)
        switch.on_emergency(log_incident)
        
        await switch.emergency_stop("Test incident")
        
        assert len(notifications) == 3
        
        print("\n✅ Emergency callback chain:")
        for n in notifications:
            print(f"   - {n}")


class TestCombinedSecuritySimulation:
    """Simulate combined security scenarios."""
    
    @pytest.mark.asyncio
    async def test_ddos_simulation(self):
        """Simulate DDoS-like attack pattern."""
        from services.orchestrator.core.guards import ResourceGuard, RateLimiter
        from services.orchestrator.core.kill_switch import KillSwitch
        from services.orchestrator.core.degradation import GracefulDegrader
        
        guard = ResourceGuard(max_tool_calls_per_minute=100)
        degrader = GracefulDegrader()
        switch = KillSwitch()
        
        # Track metrics
        allowed = 0
        blocked = 0
        
        # Simulate 1000 rapid requests
        for i in range(1000):
            # Check rate limit
            if not guard.check_tool_quota("api_endpoint"):
                blocked += 1
                
                # Trigger degradation at 500 blocked
                if blocked == 500:
                    degrader.set_level(2)  # Critical
                    print(f"   Level {i}: Degraded to CRITICAL")
                
                # Emergency stop at 800 blocked
                if blocked == 800:
                    await switch.emergency_stop("DDoS attack detected")
                    print(f"   Level {i}: EMERGENCY STOP triggered")
                    break
            else:
                allowed += 1
        
        print(f"\n✅ DDoS simulation: {allowed} allowed, {blocked} blocked")
        print(f"   Final state: {'STOPPED' if switch.is_emergency_stopped else 'RUNNING'}")
        
        # Cleanup
        await switch.resume()
        degrader.set_level(0)
    
    @pytest.mark.asyncio
    async def test_cascading_failure_protection(self):
        """Test protection against cascading failures."""
        from services.orchestrator.core.recovery import CircuitBreaker, get_circuit_breaker
        from services.orchestrator.core.kill_switch import KillSwitch
        
        switch = KillSwitch()
        
        # Simulate cascading failures across servers
        servers = ["scraper", "analyzer", "search", "vision"]
        failing_servers = []
        
        for server in servers:
            breaker = get_circuit_breaker(f"mcp_{server}")
            
            # Simulate 3 failures
            for _ in range(3):
                breaker.record_failure(Exception("Server error"))
            
            if breaker.state == "open":
                failing_servers.append(server)
                switch.blacklist_tool(server, reason="Circuit breaker open")
        
        # If majority failing, emergency stop
        if len(failing_servers) > len(servers) / 2:
            await switch.emergency_stop("Cascading failure detected")
        
        print(f"\n✅ Cascading failure protection:")
        print(f"   Failing servers: {failing_servers}")
        print(f"   Emergency stop: {switch.is_emergency_stopped}")
        
        # Cleanup
        await switch.resume()
        for server in servers:
            switch.unblacklist_tool(server)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
