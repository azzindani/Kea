"""
Unit Tests: Orchestrator Client.

Tests for HTTP client with retry, circuit breaker, and connection pooling.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from services.api_gateway.clients.orchestrator import (
    OrchestratorClient,
    CircuitBreaker,
    CircuitState,
)


class TestCircuitBreaker:
    """Test circuit breaker implementation."""
    
    def test_initial_state_closed(self):
        """Test circuit starts closed."""
        cb = CircuitBreaker()
        
        assert cb.state == CircuitState.CLOSED
        assert cb.is_open is False
    
    def test_opens_after_failures(self):
        """Test circuit opens after threshold failures."""
        cb = CircuitBreaker(failure_threshold=3)
        
        for _ in range(3):
            cb.record_failure()
        
        assert cb.state == CircuitState.OPEN
        assert cb.is_open is True
    
    def test_stays_closed_under_threshold(self):
        """Test circuit stays closed under threshold."""
        cb = CircuitBreaker(failure_threshold=5)
        
        for _ in range(3):
            cb.record_failure()
        
        assert cb.state == CircuitState.CLOSED
    
    def test_success_resets_failures(self):
        """Test success resets failure count."""
        cb = CircuitBreaker(failure_threshold=5)
        
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        
        assert cb._failure_count == 0
    
    def test_half_open_after_timeout(self):
        """Test circuit moves to half-open after timeout."""
        import time
        
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        
        time.sleep(0.15)
        
        assert cb.state == CircuitState.HALF_OPEN
    
    def test_closes_on_success_in_half_open(self):
        """Test circuit closes on success in half-open state."""
        cb = CircuitBreaker(failure_threshold=1)
        cb._state = CircuitState.HALF_OPEN
        
        cb.record_success()
        
        assert cb.state == CircuitState.CLOSED
    
    def test_opens_on_failure_in_half_open(self):
        """Test circuit opens on failure in half-open state."""
        cb = CircuitBreaker(failure_threshold=1)
        cb._state = CircuitState.HALF_OPEN
        
        cb.record_failure()
        
        assert cb.state == CircuitState.OPEN


class TestOrchestratorClient:
    """Test orchestrator HTTP client."""
    
    @pytest.fixture
    def client(self):
        """Create client for testing."""
        return OrchestratorClient(base_url="http://localhost:8000")
    
    def test_client_initialization(self, client):
        """Test client initializes correctly."""
        assert client.base_url == "http://localhost:8000"
        assert client._circuit_breaker is not None
    
    def test_custom_base_url(self):
        """Test custom base URL."""
        client = OrchestratorClient(base_url="http://custom:9000")
        
        assert client.base_url == "http://custom:9000"
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, client):
        """Test successful health check."""
        with patch.object(client, "_http") as mock_http:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
            mock_http.get = AsyncMock(return_value=mock_response)
            
            result = await client.health_check()
            
            assert result["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_requests(self, client):
        """Test circuit breaker blocks requests when open."""
        client._circuit_breaker._state = CircuitState.OPEN
        client._circuit_breaker._last_failure_time = 9999999999  # Far future
        
        with pytest.raises(Exception, match="[Cc]ircuit"):
            await client.health_check()
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self, client):
        """Test request is retried on failure."""
        call_count = 0
        
        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ConnectError("Connection failed")
            return MagicMock(status_code=200, json=lambda: {"status": "ok"})
        
        with patch.object(client, "_http") as mock_http:
            mock_http.get = failing_then_success
            
            result = await client.health_check()
            
            assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, client):
        """Test error after max retries exceeded."""
        with patch.object(client, "_http") as mock_http:
            mock_http.get = AsyncMock(side_effect=httpx.ConnectError("Failed"))
            
            with pytest.raises(httpx.ConnectError):
                await client.health_check()


class TestOrchestratorMethods:
    """Test specific orchestrator methods."""
    
    @pytest.fixture
    def client(self):
        return OrchestratorClient()
    
    @pytest.mark.asyncio
    async def test_list_tools(self, client):
        """Test listing tools."""
        with patch.object(client, "_http") as mock_http:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"tools": [{"name": "web_search"}]}
            mock_http.get = AsyncMock(return_value=mock_response)
            
            result = await client.list_tools()
            
            assert "tools" in result
            assert len(result["tools"]) == 1
    
    @pytest.mark.asyncio
    async def test_start_research(self, client):
        """Test starting research job."""
        with patch.object(client, "_http") as mock_http:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"job_id": "job-123"}
            mock_http.post = AsyncMock(return_value=mock_response)
            
            result = await client.start_research(
                query="Test query",
                depth=2,
            )
            
            assert result["job_id"] == "job-123"
    
    @pytest.mark.asyncio
    async def test_get_job_status(self, client):
        """Test getting job status."""
        with patch.object(client, "_http") as mock_http:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "job_id": "job-123",
                "status": "completed",
            }
            mock_http.get = AsyncMock(return_value=mock_response)
            
            result = await client.get_job_status("job-123")
            
            assert result["status"] == "completed"


class TestConnectionPooling:
    """Test connection pooling behavior."""
    
    def test_client_uses_pooling(self):
        """Test client uses connection pooling."""
        client = OrchestratorClient()
        
        # Client should have HTTP pool configured
        assert hasattr(client, "_http")
    
    def test_pool_limits_configured(self):
        """Test pool limits are configured."""
        client = OrchestratorClient(
            max_connections=20,
            max_keepalive=5,
        )
        
        # Limits should be set (exact check depends on implementation)
        assert client._max_connections == 20
