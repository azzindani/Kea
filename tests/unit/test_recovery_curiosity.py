"""
Tests for error recovery and circuit breaker.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from services.orchestrator.core.recovery import (
    ErrorType,
    RetryConfig,
    RetryState,
    classify_error,
    calculate_delay,
    retry,
    CircuitBreaker,
    CircuitOpenError,
    with_circuit_breaker,
    get_circuit_breaker,
)


class TestErrorType:
    """Tests for ErrorType enum."""
    
    def test_error_types(self):
        """Test error type values."""
        assert ErrorType.TRANSIENT.value == "transient"
        assert ErrorType.PERMANENT.value == "permanent"
        assert ErrorType.RESOURCE.value == "resource"
        assert ErrorType.TIMEOUT.value == "timeout"
        assert ErrorType.UNKNOWN.value == "unknown"


class TestRetryConfig:
    """Tests for RetryConfig."""
    
    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.jitter is True
    
    def test_custom_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=0.5,
            max_delay=30.0,
            jitter=False,
        )
        assert config.max_attempts == 5
        assert config.base_delay == 0.5


class TestClassifyError:
    """Tests for classify_error function."""
    
    def test_classify_timeout(self):
        """Test classifying timeout errors."""
        import asyncio
        error = asyncio.TimeoutError()
        assert classify_error(error) == ErrorType.TIMEOUT
    
    def test_classify_connection_error(self):
        """Test classifying connection errors."""
        error = ConnectionError("Connection refused")
        assert classify_error(error) == ErrorType.TRANSIENT
    
    def test_classify_value_error(self):
        """Test classifying value errors as permanent."""
        error = ValueError("Invalid input")
        assert classify_error(error) == ErrorType.PERMANENT
    
    def test_classify_memory_error(self):
        """Test classifying memory errors as resource."""
        error = MemoryError()
        assert classify_error(error) == ErrorType.RESOURCE


class TestCalculateDelay:
    """Tests for calculate_delay function."""
    
    def test_delay_increases_with_attempts(self):
        """Test that delay increases exponentially."""
        config = RetryConfig(base_delay=1.0, jitter=False)
        
        delay1 = calculate_delay(1, config, ErrorType.TRANSIENT)
        delay2 = calculate_delay(2, config, ErrorType.TRANSIENT)
        delay3 = calculate_delay(3, config, ErrorType.TRANSIENT)
        
        assert delay2 > delay1
        assert delay3 > delay2
    
    def test_delay_capped_at_max(self):
        """Test that delay is capped at max_delay."""
        config = RetryConfig(base_delay=1.0, max_delay=5.0, jitter=False)
        
        delay = calculate_delay(10, config, ErrorType.TRANSIENT)
        assert delay <= 5.0


class TestRetryDecorator:
    """Tests for retry decorator."""
    
    @pytest.mark.asyncio
    async def test_retry_succeeds_first_try(self):
        """Test that successful function doesn't retry."""
        call_count = 0
        
        @retry(max_attempts=3)
        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await success_func()
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test that function retries on failure."""
        call_count = 0
        
        @retry(max_attempts=3, base_delay=0.01)
        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Transient error")
            return "success"
        
        result = await fail_then_succeed()
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        """Test that exception is raised after max attempts."""
        call_count = 0
        
        @retry(max_attempts=3, base_delay=0.01)
        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Always fails")
        
        with pytest.raises(ConnectionError):
            await always_fail()
        
        assert call_count == 3


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""
    
    @pytest.fixture
    def breaker(self):
        return CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=0.1,
            half_open_requests=1,
        )
    
    def test_initial_state_closed(self, breaker):
        """Test that circuit starts closed."""
        assert breaker.state == "closed"
    
    def test_opens_after_failures(self, breaker):
        """Test that circuit opens after failure threshold."""
        for _ in range(3):
            breaker.record_failure(ConnectionError("Error"))
        
        assert breaker.state == "open"
    
    def test_record_success_resets_failures(self, breaker):
        """Test that success resets failure count."""
        breaker.record_failure(ConnectionError("Error"))
        breaker.record_failure(ConnectionError("Error"))
        breaker.record_success()
        
        assert breaker._failures == 0
        assert breaker.state == "closed"
    
    @pytest.mark.asyncio
    async def test_context_manager_success(self, breaker):
        """Test circuit breaker as context manager with success."""
        async with breaker:
            pass  # Simulates successful operation
        
        assert breaker.state == "closed"
    
    @pytest.mark.asyncio
    async def test_context_manager_failure(self, breaker):
        """Test circuit breaker as context manager with failure."""
        try:
            async with breaker:
                raise ConnectionError("Error")
        except ConnectionError:
            pass
        
        assert breaker._failures == 1


class TestGetCircuitBreaker:
    """Tests for get_circuit_breaker function."""
    
    def test_creates_new_breaker(self):
        """Test that new breaker is created for new name."""
        breaker = get_circuit_breaker("test_service")
        assert isinstance(breaker, CircuitBreaker)
    
    def test_returns_same_breaker(self):
        """Test that same breaker is returned for same name."""
        breaker1 = get_circuit_breaker("my_service")
        breaker2 = get_circuit_breaker("my_service")
        assert breaker1 is breaker2


class TestWithCircuitBreaker:
    """Tests for with_circuit_breaker decorator."""
    
    @pytest.mark.asyncio
    async def test_decorator_wraps_function(self):
        """Test that decorator wraps function."""
        breaker = CircuitBreaker()
        
        @with_circuit_breaker(breaker)
        async def my_func():
            return "result"
        
        result = await my_func()
        assert result == "result"
