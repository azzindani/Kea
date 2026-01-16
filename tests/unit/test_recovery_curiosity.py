"""
Tests for error recovery with retry and circuit breaker.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock


class TestErrorType:
    """Tests for ErrorType enum."""
    
    def test_import_error_type(self):
        """Test that ErrorType can be imported."""
        from services.orchestrator.core.recovery import ErrorType
        assert ErrorType is not None
    
    def test_error_type_values(self):
        """Test error type values."""
        from services.orchestrator.core.recovery import ErrorType
        
        assert ErrorType.TRANSIENT.value == "transient"
        assert ErrorType.PERMANENT.value == "permanent"
        assert ErrorType.RESOURCE.value == "resource"
        assert ErrorType.TIMEOUT.value == "timeout"
        assert ErrorType.UNKNOWN.value == "unknown"


class TestRetryConfig:
    """Tests for RetryConfig dataclass."""
    
    def test_import_retry_config(self):
        """Test that RetryConfig can be imported."""
        from services.orchestrator.core.recovery import RetryConfig
        assert RetryConfig is not None
    
    def test_default_config(self):
        """Test default retry configuration."""
        from services.orchestrator.core.recovery import RetryConfig
        
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.jitter is True


class TestClassifyError:
    """Tests for classify_error function."""
    
    def test_import_classify_error(self):
        """Test that classify_error can be imported."""
        from services.orchestrator.core.recovery import classify_error
        assert classify_error is not None
    
    def test_classify_connection_error(self):
        """Test classifying connection error."""
        from services.orchestrator.core.recovery import classify_error, ErrorType
        
        error = ConnectionError("Connection refused")
        result = classify_error(error)
        
        assert result == ErrorType.TRANSIENT
    
    def test_classify_value_error(self):
        """Test classifying value error."""
        from services.orchestrator.core.recovery import classify_error, ErrorType
        
        error = ValueError("Invalid value")
        result = classify_error(error)
        
        assert result == ErrorType.PERMANENT


class TestCalculateDelay:
    """Tests for calculate_delay function."""
    
    def test_import_calculate_delay(self):
        """Test that calculate_delay can be imported."""
        from services.orchestrator.core.recovery import calculate_delay
        assert calculate_delay is not None
    
    def test_delay_increases_with_attempts(self):
        """Test delay increases with attempts."""
        from services.orchestrator.core.recovery import (
            calculate_delay, RetryConfig, ErrorType
        )
        
        config = RetryConfig(base_delay=1.0, jitter=False)
        
        delay1 = calculate_delay(1, config, ErrorType.TRANSIENT)
        delay2 = calculate_delay(2, config, ErrorType.TRANSIENT)
        
        assert delay2 > delay1


class TestRetryDecorator:
    """Tests for retry decorator."""
    
    def test_import_retry(self):
        """Test that retry can be imported."""
        from services.orchestrator.core.recovery import retry
        assert retry is not None
    
    @pytest.mark.asyncio
    async def test_retry_success(self):
        """Test retry with successful function."""
        from services.orchestrator.core.recovery import retry
        
        @retry(max_attempts=3)
        async def successful_func():
            return "success"
        
        result = await successful_func()
        assert result == "success"


class TestCircuitBreaker:
    """Tests for CircuitBreaker class."""
    
    def test_import_circuit_breaker(self):
        """Test that CircuitBreaker can be imported."""
        from services.orchestrator.core.recovery import (
            CircuitBreaker,
            CircuitOpenError,
        )
        assert CircuitBreaker is not None
    
    def test_create_circuit_breaker(self):
        """Test creating circuit breaker."""
        from services.orchestrator.core.recovery import CircuitBreaker
        
        breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30.0,
        )
        
        assert breaker.failure_threshold == 3
        assert breaker.recovery_timeout == 30.0
    
    def test_initial_state_closed(self):
        """Test initial state is closed."""
        from services.orchestrator.core.recovery import CircuitBreaker
        
        breaker = CircuitBreaker()
        assert breaker.state == "closed"
    
    def test_record_failure(self):
        """Test recording failure."""
        from services.orchestrator.core.recovery import CircuitBreaker
        
        breaker = CircuitBreaker(failure_threshold=3)
        
        breaker.record_failure(Exception("test"))
        breaker.record_failure(Exception("test"))
        
        assert breaker._failures == 2
    
    def test_opens_after_threshold(self):
        """Test circuit opens after threshold failures."""
        from services.orchestrator.core.recovery import CircuitBreaker
        
        breaker = CircuitBreaker(failure_threshold=2)
        
        breaker.record_failure(Exception("test"))
        breaker.record_failure(Exception("test"))
        
        assert breaker.state == "open"
    
    def test_record_success(self):
        """Test recording success."""
        from services.orchestrator.core.recovery import CircuitBreaker
        
        breaker = CircuitBreaker()
        breaker.record_success()
        
        assert breaker.state == "closed"


class TestGetCircuitBreaker:
    """Tests for get_circuit_breaker function."""
    
    def test_import_get_circuit_breaker(self):
        """Test that get_circuit_breaker can be imported."""
        from services.orchestrator.core.recovery import get_circuit_breaker
        assert get_circuit_breaker is not None
    
    def test_get_named_circuit_breaker(self):
        """Test getting named circuit breaker."""
        from services.orchestrator.core.recovery import (
            get_circuit_breaker, CircuitBreaker
        )
        
        breaker = get_circuit_breaker("test_service")
        assert isinstance(breaker, CircuitBreaker)
    
    def test_same_name_returns_same_breaker(self):
        """Test same name returns same breaker."""
        from services.orchestrator.core.recovery import get_circuit_breaker
        
        breaker1 = get_circuit_breaker("same_service")
        breaker2 = get_circuit_breaker("same_service")
        
        assert breaker1 is breaker2
