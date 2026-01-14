"""
Tests for Graceful Degradation and Error Recovery.
"""

import pytest
import asyncio


class TestGracefulDegradation:
    """Tests for graceful degradation."""
    
    def test_degradation_levels(self):
        """Test degradation level definitions."""
        from services.orchestrator.core.degradation import GracefulDegrader
        
        degrader = GracefulDegrader(base_parallel=4, base_batch_size=1000)
        
        # Normal level
        level0 = degrader.get_current_level()
        assert level0.level == 0
        assert level0.max_parallel == 4
        assert level0.batch_size == 1000
        assert level0.skip_optional_tasks is False
        
        # Warning level
        degrader.set_level(1)
        level1 = degrader.get_current_level()
        assert level1.level == 1
        assert level1.max_parallel == 2  # Halved
        assert level1.batch_size == 500   # Halved
        
        # Critical level
        degrader.set_level(2)
        level2 = degrader.get_current_level()
        assert level2.level == 2
        assert level2.max_parallel == 1
        assert level2.skip_optional_tasks is True
        
        print("\n✅ Degradation levels work correctly")
    
    @pytest.mark.asyncio
    async def test_throttle_context(self):
        """Test throttle context manager."""
        from services.orchestrator.core.degradation import GracefulDegrader
        
        degrader = GracefulDegrader(base_parallel=2)
        
        # Run multiple concurrent tasks through throttle
        async def work(n: int) -> int:
            async with degrader.throttle():
                await asyncio.sleep(0.1)
                return n
        
        results = await asyncio.gather(*[work(i) for i in range(5)])
        assert len(results) == 5
        
        print("\n✅ Throttle context works correctly")
    
    def test_timeout_adjustment(self):
        """Test timeout adjustment based on level."""
        from services.orchestrator.core.degradation import GracefulDegrader
        
        degrader = GracefulDegrader(base_timeout=30.0)
        
        # Normal
        assert degrader.get_timeout() == 30.0
        
        # Warning (1.5x)
        degrader.set_level(1)
        assert degrader.get_timeout() == 45.0
        
        # Critical (2x)
        degrader.set_level(2)
        assert degrader.get_timeout() == 60.0
        
        print("\n✅ Timeout adjustment works correctly")


class TestErrorRecovery:
    """Tests for error recovery."""
    
    def test_error_classification(self):
        """Test error classification."""
        from services.orchestrator.core.recovery import classify_error, ErrorType
        
        # Transient
        assert classify_error(Exception("Rate limit exceeded")) == ErrorType.TRANSIENT
        assert classify_error(Exception("429 Too Many Requests")) == ErrorType.TRANSIENT
        assert classify_error(ConnectionError("Connection refused")) == ErrorType.TRANSIENT
        
        # Permanent
        assert classify_error(Exception("Authentication failed")) == ErrorType.PERMANENT
        assert classify_error(Exception("403 Forbidden")) == ErrorType.PERMANENT
        assert classify_error(Exception("Invalid input")) == ErrorType.PERMANENT
        
        # Timeout
        assert classify_error(Exception("Request timed out")) == ErrorType.TIMEOUT
        
        # Resource
        assert classify_error(Exception("Out of memory")) == ErrorType.RESOURCE
        
        print("\n✅ Error classification works correctly")
    
    @pytest.mark.asyncio
    async def test_retry_success(self):
        """Test retry decorator with eventual success."""
        from services.orchestrator.core.recovery import retry
        
        attempt_count = 0
        
        @retry(max_attempts=3, base_delay=0.1)
        async def flaky_operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise Exception("Transient error")
            return "success"
        
        result = await flaky_operation()
        assert result == "success"
        assert attempt_count == 2  # Failed once, succeeded on second
        
        print("\n✅ Retry with eventual success works")
    
    @pytest.mark.asyncio
    async def test_retry_failure(self):
        """Test retry decorator exhaustion."""
        from services.orchestrator.core.recovery import retry
        
        @retry(max_attempts=2, base_delay=0.05)
        async def always_fails():
            raise Exception("Always fails")
        
        with pytest.raises(Exception, match="Always fails"):
            await always_fails()
        
        print("\n✅ Retry exhaustion works correctly")
    
    @pytest.mark.asyncio
    async def test_circuit_breaker(self):
        """Test circuit breaker pattern."""
        from services.orchestrator.core.recovery import CircuitBreaker, CircuitOpenError
        
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.5)
        
        # Initial state is closed
        assert breaker.state == "closed"
        
        # Record failures
        breaker.record_failure(Exception("fail 1"))
        breaker.record_failure(Exception("fail 2"))
        
        # Should be open now
        assert breaker.state == "open"
        
        # Should raise when trying to use
        with pytest.raises(CircuitOpenError):
            async with breaker:
                pass
        
        # Wait for recovery
        await asyncio.sleep(0.6)
        
        # Should be half-open now
        assert breaker.state == "half_open"
        
        print("\n✅ Circuit breaker works correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
