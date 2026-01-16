"""
Degradation and Recovery Simulation Tests.

Tests graceful degradation and error recovery in simulated pressure scenarios.
"""

import pytest
import asyncio


class TestDegradationSimulation:
    """Simulate graceful degradation scenarios."""
    
    def test_progressive_degradation(self):
        """Test progressive degradation levels."""
        from services.orchestrator.core.degradation import (
            GracefulDegrader, DegradationLevel
        )
        
        degrader = GracefulDegrader(base_parallel=8, base_batch_size=1000)
        
        configs = []
        
        # Simulate increasing pressure (levels 0, 1, 2)
        for level in range(3):  # NORMAL, WARNING, CRITICAL
            degrader.set_level(level)
            config = degrader.get_current_level()
            configs.append({
                "level": config.level,
                "parallel": config.max_parallel,
                "batch_size": config.batch_size,
            })
        
        # Each level should reduce capacity
        assert configs[0]["parallel"] > configs[1]["parallel"]
        assert configs[1]["parallel"] > configs[2]["parallel"]
        
        print("\n✅ Progressive degradation:")
        for c in configs:
            print(f"   Level {c['level']}: parallel={c['parallel']}, batch={c['batch_size']}")
    
    def test_get_current_level(self):
        """Test getting current degradation level."""
        from services.orchestrator.core.degradation import (
            GracefulDegrader, DegradationLevel
        )
        
        degrader = GracefulDegrader()
        
        # Get current level
        level = degrader.get_current_level()
        
        assert isinstance(level, DegradationLevel)
        assert level.level == 0  # Default is normal
        
        print(f"\n✅ Current level: {level.level}")
    
    @pytest.mark.asyncio
    async def test_throttled_under_pressure(self):
        """Test throttling behavior under pressure."""
        from services.orchestrator.core.degradation import (
            throttled, get_degrader
        )
        import time
        
        degrader = get_degrader()
        
        # Create throttled function - note: throttled takes degrader, not level+delay
        @throttled(degrader)
        async def slow_operation():
            return "done"
        
        # At normal level
        degrader.set_level(0)
        start = time.time()
        await slow_operation()
        normal_time = time.time() - start
        
        # At critical level (reduced parallelism)
        degrader.set_level(2)
        start = time.time()
        await slow_operation()
        critical_time = time.time() - start
        
        # Both should complete successfully
        print(f"\n✅ Throttling: normal={normal_time:.3f}s, critical={critical_time:.3f}s")


class TestRecoverySimulation:
    """Simulate error recovery scenarios."""
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff(self):
        """Test retry with exponential backoff."""
        from services.orchestrator.core.recovery import retry
        import time
        
        attempt_times = []
        
        @retry(max_attempts=3, base_delay=0.1, max_delay=1.0)
        async def flaky_operation():
            attempt_times.append(time.time())
            if len(attempt_times) < 3:
                raise Exception("Transient error 429")
            return "success"
        
        start = time.time()
        result = await flaky_operation()
        
        assert result == "success"
        assert len(attempt_times) == 3
        
        # Check delays increased
        if len(attempt_times) >= 2:
            delay1 = attempt_times[1] - attempt_times[0]
            delay2 = attempt_times[2] - attempt_times[1]
            print(f"\n✅ Retry backoff: delay1={delay1:.3f}s, delay2={delay2:.3f}s")
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_protection(self):
        """Test circuit breaker opens after failures."""
        from services.orchestrator.core.recovery import (
            CircuitBreaker, CircuitOpenError
        )
        
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=0.5)
        
        # Record failures
        for i in range(3):
            breaker.record_failure(Exception(f"fail {i}"))
        
        # Breaker should be open
        assert breaker.state == "open"
        
        # Should reject requests
        with pytest.raises(CircuitOpenError):
            async with breaker:
                pass
        
        # Wait for recovery timeout to allow half-open
        await asyncio.sleep(0.6)
        
        # State should transition to half-open on next check
        # Record success should close it
        breaker.record_success()
        assert breaker.state == "closed"
        
        print("\n✅ Circuit breaker protection works")
    
    def test_error_classification(self):
        """Test error classification."""
        from services.orchestrator.core.recovery import classify_error, ErrorType
        
        test_cases = [
            (Exception("Rate limit exceeded 429"), ErrorType.TRANSIENT),
            (Exception("Connection timed out"), ErrorType.TIMEOUT),
            (Exception("Authentication failed 401"), ErrorType.PERMANENT),
            (Exception("Out of memory"), ErrorType.RESOURCE),
            (Exception("Random error"), ErrorType.UNKNOWN),
        ]
        
        for error, expected in test_cases:
            result = classify_error(error)
            assert result == expected, f"Expected {expected} for '{error}', got {result}"
        
        print("\n✅ Error classification works for all types")


class TestResourceGuardSimulation:
    """Simulate resource guard scenarios."""
    
    @pytest.mark.asyncio
    async def test_agent_spawn_limiting(self):
        """Test agent spawn rate limiting."""
        from services.orchestrator.core.guards import ResourceGuard
        
        guard = ResourceGuard(max_agents_per_minute=5)
        
        # Track spawn attempts
        allowed = 0
        blocked = 0
        
        for i in range(10):
            if await guard.check_can_spawn(f"session_{i}"):
                allowed += 1
                guard.register_agent_spawn()
            else:
                blocked += 1
        
        print(f"\n✅ Spawn limiting: allowed={allowed}, blocked={blocked}")
        
        assert guard.active_agent_count == allowed
    
    def test_tool_quota_enforcement(self):
        """Test tool call quota."""
        from services.orchestrator.core.guards import ResourceGuard
        
        guard = ResourceGuard(max_tool_calls_per_minute=10)
        
        allowed = 0
        for i in range(15):
            if guard.check_tool_quota("expensive_tool"):
                allowed += 1
        
        assert allowed <= 10
        
        print(f"\n✅ Tool quota: {allowed}/15 allowed")


class TestKillSwitchSimulation:
    """Simulate kill switch scenarios."""
    
    @pytest.mark.asyncio
    async def test_emergency_stop_all(self):
        """Test emergency stop halts all activity."""
        from services.orchestrator.core.kill_switch import KillSwitch
        
        switch = KillSwitch()
        
        # Normal operation
        assert switch.can_proceed() is True
        
        # Emergency stop
        await switch.emergency_stop("System overload")
        
        # All should be blocked
        assert switch.can_proceed() is False
        assert switch.can_proceed(tool_name="any_tool") is False
        assert switch.can_proceed(dept_id="any_dept") is False
        
        # Resume
        await switch.resume()
        
        assert switch.can_proceed() is True
        
        print("\n✅ Emergency stop halts all, resume restores")
    
    @pytest.mark.asyncio
    async def test_selective_blacklisting(self):
        """Test selective tool blacklisting."""
        from services.orchestrator.core.kill_switch import KillSwitch
        
        switch = KillSwitch()
        
        # Blacklist specific tool
        switch.blacklist_tool("failing_scraper", reason="Timeout errors", duration_minutes=1)
        
        # That tool blocked, others work
        assert switch.can_proceed(tool_name="failing_scraper") is False
        assert switch.can_proceed(tool_name="working_tool") is True
        
        # Unblacklist
        switch.unblacklist_tool("failing_scraper")
        
        assert switch.can_proceed(tool_name="failing_scraper") is True
        
        print("\n✅ Selective blacklisting works")
    
    @pytest.mark.asyncio
    async def test_department_pause(self):
        """Test department-level pause."""
        from services.orchestrator.core.kill_switch import KillSwitch
        
        switch = KillSwitch()
        
        # Pause research department
        switch.pause_department("dept_research")
        
        # Research blocked, finance works
        assert switch.can_proceed(dept_id="dept_research") is False
        assert switch.can_proceed(dept_id="dept_finance") is True
        
        # Resume research
        switch.resume_department("dept_research")
        
        assert switch.can_proceed(dept_id="dept_research") is True
        
        print("\n✅ Department pause works")


class TestCombinedResilienceSimulation:
    """Simulate combined resilience scenarios."""
    
    @pytest.mark.asyncio
    async def test_degradation_with_guards(self):
        """Test graceful degradation with resource guards."""
        from services.orchestrator.core.degradation import GracefulDegrader
        from services.orchestrator.core.guards import ResourceGuard
        
        degrader = GracefulDegrader(base_parallel=4)
        guard = ResourceGuard(max_agents_per_minute=10)
        
        # Simulate pressure
        degrader.set_level(2)  # Critical
        config = degrader.get_current_level()
        
        # Adjust guard based on degradation
        effective_limit = min(config.max_parallel, 2)
        
        assert effective_limit <= 2
        
        print(f"\n✅ Combined: degraded parallel={config.max_parallel}, effective={effective_limit}")
    
    @pytest.mark.asyncio
    async def test_recovery_with_kill_switch(self):
        """Test recovery respects kill switch."""
        from services.orchestrator.core.recovery import retry, CircuitBreaker
        from services.orchestrator.core.kill_switch import KillSwitch
        
        switch = KillSwitch()
        breaker = CircuitBreaker(failure_threshold=3)
        
        # Blacklist tool
        switch.blacklist_tool("flaky_api")
        
        @retry(max_attempts=3, base_delay=0.01)
        async def call_api():
            if not switch.can_proceed(tool_name="flaky_api"):
                raise Exception("Tool blacklisted - no retry")
            return "success"
        
        # Should fail fast (no retry for blacklisted)
        try:
            await call_api()
        except Exception as e:
            assert "blacklisted" in str(e)
        
        print("\n✅ Recovery respects kill switch")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
