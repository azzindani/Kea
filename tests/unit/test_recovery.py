"""
Tests for Error Recovery with Retry and Backoff.
"""

import pytest
import asyncio


class TestErrorType:
    """Tests for error classification."""
    
    def test_error_types(self):
        """Test error type values."""
        from services.orchestrator.core.recovery import ErrorType
        
        assert ErrorType.TRANSIENT.value == "transient"
        assert ErrorType.PERMANENT.value == "permanent"
        assert ErrorType.RESOURCE.value == "resource"
        assert ErrorType.TIMEOUT.value == "timeout"
        assert ErrorType.UNKNOWN.value == "unknown"
        
        print("\n✅ ErrorType values correct")


class TestClassifyError:
    """Tests for error classification function."""
    
    def test_classify_rate_limit(self):
        """Test rate limit error classification."""
        from services.orchestrator.core.recovery import classify_error, ErrorType
        
        error = Exception("Rate limit exceeded (429)")
        assert classify_error(error) == ErrorType.TRANSIENT
        
        error = Exception("Too many requests")
        assert classify_error(error) == ErrorType.TRANSIENT
        
        print("\n✅ Rate limit classified as transient")
    
    def test_classify_timeout(self):
        """Test timeout error classification."""
        from services.orchestrator.core.recovery import classify_error, ErrorType
        
        error = Exception("Connection timed out")
        assert classify_error(error) == ErrorType.TIMEOUT
        
        error = Exception("Request timeout after 30s")
        assert classify_error(error) == ErrorType.TIMEOUT
        
        print("\n✅ Timeout classified correctly")
    
    def test_classify_auth_error(self):
        """Test auth error classification."""
        from services.orchestrator.core.recovery import classify_error, ErrorType
        
        error = Exception("Authentication failed (401)")
        assert classify_error(error) == ErrorType.PERMANENT
        
        error = Exception("Forbidden (403)")
        assert classify_error(error) == ErrorType.PERMANENT
        
        print("\n✅ Auth errors classified as permanent")
    
    def test_classify_resource_error(self):
        """Test resource error classification."""
        from services.orchestrator.core.recovery import classify_error, ErrorType
        
        error = Exception("Out of memory")
        assert classify_error(error) == ErrorType.RESOURCE
        
        error = Exception("Disk space full")
        assert classify_error(error) == ErrorType.RESOURCE
        
        print("\n✅ Resource errors classified correctly")
    
    def test_classify_validation_error(self):
        """Test validation error classification."""
        from services.orchestrator.core.recovery import classify_error, ErrorType
        
        error = Exception("Invalid input format")
        assert classify_error(error) == ErrorType.PERMANENT
        
        error = Exception("Required field missing")
        assert classify_error(error) == ErrorType.PERMANENT
        
        print("\n✅ Validation errors classified as permanent")


class TestRetryConfig:
    """Tests for retry configuration."""
    
    def test_default_config(self):
        """Test default retry config."""
        from services.orchestrator.core.recovery import RetryConfig
        
        config = RetryConfig()
        
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.jitter is True
        
        print("\n✅ Default config correct")
    
    def test_custom_config(self):
        """Test custom retry config."""
        from services.orchestrator.core.recovery import RetryConfig
        
        config = RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            max_delay=120.0,
            jitter=False,
        )
        
        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.jitter is False
        
        print("\n✅ Custom config works")


class TestCalculateDelay:
    """Tests for delay calculation."""
    
    def test_exponential_backoff(self):
        """Test exponential backoff calculation."""
        from services.orchestrator.core.recovery import (
            calculate_delay, RetryConfig, ErrorType
        )
        
        config = RetryConfig(base_delay=1.0, jitter=False)
        
        delay0 = calculate_delay(0, config, ErrorType.TRANSIENT)
        delay1 = calculate_delay(1, config, ErrorType.TRANSIENT)
        delay2 = calculate_delay(2, config, ErrorType.TRANSIENT)
        
        # Should increase exponentially
        assert delay1 > delay0
        assert delay2 > delay1
        
        print(f"\n✅ Exponential backoff: {delay0:.1f}s → {delay1:.1f}s → {delay2:.1f}s")
    
    def test_delay_capped_at_max(self):
        """Test delay is capped at max."""
        from services.orchestrator.core.recovery import (
            calculate_delay, RetryConfig, ErrorType
        )
        
        config = RetryConfig(base_delay=10.0, max_delay=30.0, jitter=False)
        
        # High attempt should still cap at max
        delay = calculate_delay(10, config, ErrorType.TRANSIENT)
        
        assert delay <= 30.0
        
        print(f"\n✅ Delay capped at max: {delay:.1f}s")


class TestRetryDecorator:
    """Tests for @retry decorator."""
    
    @pytest.mark.asyncio
    async def test_retry_on_success(self):
        """Test retry on immediate success."""
        from services.orchestrator.core.recovery import retry
        
        call_count = 0
        
        @retry(max_attempts=3)
        async def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await successful_func()
        
        assert result == "success"
        assert call_count == 1  # Only called once
        
        print("\n✅ Retry on success: 1 attempt")
    
    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self):
        """Test retry on transient error."""
        from services.orchestrator.core.recovery import retry
        
        call_count = 0
        
        @retry(max_attempts=3, base_delay=0.01)  # Fast for testing
        async def failing_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Rate limit 429")
            return "success after retries"
        
        result = await failing_twice()
        
        assert result == "success after retries"
        assert call_count == 3
        
        print(f"\n✅ Retry on transient: {call_count} attempts")
    
    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        """Test all retries exhausted."""
        from services.orchestrator.core.recovery import retry
        
        @retry(max_attempts=2, base_delay=0.01)
        async def always_fails():
            raise Exception("Always fails")
        
        with pytest.raises(Exception) as exc_info:
            await always_fails()
        
        assert "Always fails" in str(exc_info.value)
        
        print("\n✅ Retry exhaustion raises exception")
    
    @pytest.mark.asyncio
    async def test_no_retry_on_permanent(self):
        """Test no retry on permanent errors."""
        from services.orchestrator.core.recovery import retry
        
        call_count = 0
        
        @retry(max_attempts=5, base_delay=0.01)
        async def auth_error():
            nonlocal call_count
            call_count += 1
            raise Exception("Authentication failed 401")
        
        with pytest.raises(Exception):
            await auth_error()
        
        # Should only call once (permanent = no retry)
        assert call_count == 1
        
        print("\n✅ Permanent errors not retried")


class TestCircuitBreaker:
    """Tests for circuit breaker."""
    
    def test_create_breaker(self):
        """Test circuit breaker creation."""
        from services.orchestrator.core.recovery import CircuitBreaker
        
        breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0,
        )
        
        assert breaker.state == "closed"
        
        print("\n✅ CircuitBreaker created (closed)")
    
    def test_breaker_opens_after_failures(self):
        """Test breaker opens after threshold failures."""
        from services.orchestrator.core.recovery import CircuitBreaker
        
        breaker = CircuitBreaker(failure_threshold=3)
        
        # Record 3 failures
        for _ in range(3):
            breaker.record_failure(Exception("fail"))
        
        assert breaker.state == "open"
        
        print("\n✅ Breaker opens after failures")
    
    def test_breaker_rejects_when_open(self):
        """Test breaker rejects requests when open."""
        from services.orchestrator.core.recovery import (
            CircuitBreaker, CircuitOpenError
        )
        import asyncio
        
        breaker = CircuitBreaker(failure_threshold=1)
        breaker.record_failure(Exception("fail"))
        
        async def try_enter():
            async with breaker:
                return "allowed"
        
        with pytest.raises(CircuitOpenError):
            asyncio.run(try_enter())
        
        print("\n✅ Open breaker rejects requests")
    
    def test_breaker_records_success(self):
        """Test breaker records success."""
        from services.orchestrator.core.recovery import CircuitBreaker
        
        breaker = CircuitBreaker()
        
        breaker.record_success()
        breaker.record_success()
        
        assert breaker.state == "closed"
        
        print("\n✅ Success keeps breaker closed")
    
    def test_get_circuit_breaker(self):
        """Test named circuit breaker retrieval."""
        from services.orchestrator.core.recovery import get_circuit_breaker
        
        b1 = get_circuit_breaker("api_server")
        b2 = get_circuit_breaker("api_server")
        b3 = get_circuit_breaker("other_server")
        
        assert b1 is b2  # Same name = same breaker
        assert b1 is not b3  # Different name = different breaker
        
        print("\n✅ Named circuit breakers work")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
