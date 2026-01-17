"""
Tests for OrchestratorClient.
"""

import pytest
import time
from unittest.mock import patch, AsyncMock, MagicMock

import httpx


class TestCircuitState:
    """Tests for CircuitState enum."""
    
    def test_import_circuit_state(self):
        """Test that CircuitState can be imported."""
        from services.api_gateway.clients.orchestrator import CircuitState
        assert CircuitState is not None
    
    def test_circuit_states(self):
        """Test circuit states."""
        from services.api_gateway.clients.orchestrator import CircuitState
        
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""
    
    def test_import_circuit_breaker(self):
        """Test that CircuitBreaker can be imported."""
        from services.api_gateway.clients.orchestrator import CircuitBreaker
        assert CircuitBreaker is not None
    
    def test_initial_state_closed(self):
        """Test initial state is closed."""
        from services.api_gateway.clients.orchestrator import CircuitBreaker, CircuitState
        
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert cb.can_execute() is True
    
    def test_opens_after_failures(self):
        """Test circuit opens after threshold failures."""
        from services.api_gateway.clients.orchestrator import CircuitBreaker, CircuitState
        
        cb = CircuitBreaker(failure_threshold=3)
        
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        
        assert cb.state == CircuitState.OPEN
        assert cb.can_execute() is False
    
    def test_stays_closed_under_threshold(self):
        """Test circuit stays closed under threshold."""
        from services.api_gateway.clients.orchestrator import CircuitBreaker, CircuitState
        
        cb = CircuitBreaker(failure_threshold=5)
        
        cb.record_failure()
        cb.record_failure()
        
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 2
    
    def test_success_resets_failures(self):
        """Test success resets failure count."""
        from services.api_gateway.clients.orchestrator import CircuitBreaker
        
        cb = CircuitBreaker(failure_threshold=5)
        
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        
        assert cb.failure_count == 0


class TestOrchestratorClient:
    """Tests for OrchestratorClient."""
    
    def test_import_client(self):
        """Test that OrchestratorClient can be imported."""
        from services.api_gateway.clients.orchestrator import (
            OrchestratorClient,
            get_orchestrator_client,
        )
        assert OrchestratorClient is not None
    
    def test_client_initialization(self):
        """Test client initialization."""
        from services.api_gateway.clients.orchestrator import OrchestratorClient
        
        client = OrchestratorClient(base_url="http://test:8000")
        assert client.base_url == "http://test:8000"
    
    def test_custom_base_url(self):
        """Test custom base URL."""
        from services.api_gateway.clients.orchestrator import OrchestratorClient
        
        client = OrchestratorClient(base_url="http://custom:9000")
        assert client.base_url == "http://custom:9000"
    
    @pytest.mark.asyncio
    async def test_close(self):
        """Test client close."""
        from services.api_gateway.clients.orchestrator import OrchestratorClient
        
        client = OrchestratorClient()
        await client.close()
        # Should not raise


class TestOrchestratorMethods:
    """Tests for OrchestratorClient methods."""
    
    @pytest.mark.asyncio
    async def test_health_check_mock(self):
        """Test health check with mock."""
        from services.api_gateway.clients.orchestrator import OrchestratorClient
        
        client = OrchestratorClient()
        client._client = MagicMock()
        client._client.is_closed = False
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        
        client._client.request = AsyncMock(return_value=mock_response)
        
        result = await client.health_check()
        assert result["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_list_tools_mock(self):
        """Test list tools with mock."""
        from services.api_gateway.clients.orchestrator import OrchestratorClient
        
        client = OrchestratorClient()
        client._client = MagicMock()
        client._client.is_closed = False
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tools": [{"name": "search"}]}
        
        client._client.request = AsyncMock(return_value=mock_response)
        
        result = await client.list_tools()
        assert len(result) == 1
        assert result[0]["name"] == "search"
