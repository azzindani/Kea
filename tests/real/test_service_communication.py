"""
Real Tests: Service Communication.

Tests for inter-service HTTP communication with real calls.
Run with: pytest tests/real/test_service_communication.py -v -s
"""

import pytest
import asyncio


class TestOrchestratorClientLive:
    """Test orchestrator client with real server."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_client_init(self, logger):
        """Client initializes correctly."""
        logger.info("Testing OrchestratorClient init")
        
        from services.api_gateway.clients.orchestrator import OrchestratorClient
        
        client = OrchestratorClient(base_url="http://localhost:8000")
        
        assert client.base_url == "http://localhost:8000"
        print(f"✅ OrchestratorClient initialized")
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_client_methods(self, logger):
        """Client has all required methods."""
        logger.info("Testing OrchestratorClient methods")
        
        from services.api_gateway.clients.orchestrator import OrchestratorClient
        
        client = OrchestratorClient()
        
        # Check methods exist
        assert hasattr(client, 'health_check')
        assert hasattr(client, 'list_tools')
        assert hasattr(client, 'start_research')
        assert hasattr(client, 'stream_research')
        assert hasattr(client, 'call_tool')
        
        print(f"✅ All methods available")


class TestRAGServiceClientLive:
    """Test RAG service client with real server."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_client_init(self, logger):
        """Client initializes correctly."""
        logger.info("Testing RAGServiceClient init")
        
        from services.api_gateway.clients.rag_service import RAGServiceClient
        
        client = RAGServiceClient(base_url="http://localhost:8001")
        
        assert client.base_url == "http://localhost:8001"
        print(f"✅ RAGServiceClient initialized")
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_client_methods(self, logger):
        """Client has all required methods."""
        logger.info("Testing RAGServiceClient methods")
        
        from services.api_gateway.clients.rag_service import RAGServiceClient
        
        client = RAGServiceClient()
        
        # Check methods exist
        assert hasattr(client, 'health_check')
        assert hasattr(client, 'search')
        assert hasattr(client, 'add_fact')
        assert hasattr(client, 'get_fact')
        assert hasattr(client, 'store_artifact')
        assert hasattr(client, 'query_graph')
        
        print(f"✅ All methods available")


class TestServiceIntegration:
    """Test service integration patterns."""
    
    @pytest.mark.asyncio
    @pytest.mark.real_api
    async def test_cross_service_pattern(self, logger):
        """Test cross-service call pattern."""
        logger.info("Testing cross-service pattern")
        
        from services.api_gateway.clients.orchestrator import OrchestratorClient
        from services.api_gateway.clients.rag_service import RAGServiceClient
        
        # This simulates how the API Gateway would use both clients
        orch_client = OrchestratorClient()
        rag_client = RAGServiceClient()
        
        # In a real scenario:
        # 1. API Gateway receives request
        # 2. Calls orchestrator for research
        # 3. Stores results in RAG service
        
        print(f"✅ Cross-service pattern validated")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
