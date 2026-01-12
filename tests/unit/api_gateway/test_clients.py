"""
Unit Tests: Service Clients.

Tests for services/api_gateway/clients/*.py
"""

import pytest


class TestOrchestratorClient:
    """Tests for orchestrator client."""
    
    def test_client_init(self):
        """Client initializes correctly."""
        from services.api_gateway.clients.orchestrator import OrchestratorClient
        
        client = OrchestratorClient()
        
        assert client.base_url is not None
        assert client.timeout is not None
    
    def test_client_custom_url(self):
        """Client accepts custom URL."""
        from services.api_gateway.clients.orchestrator import OrchestratorClient
        
        client = OrchestratorClient(base_url="http://custom:9000")
        
        assert client.base_url == "http://custom:9000"


class TestRAGServiceClient:
    """Tests for RAG service client."""
    
    def test_client_init(self):
        """Client initializes correctly."""
        from services.api_gateway.clients.rag_service import RAGServiceClient
        
        client = RAGServiceClient()
        
        assert client.base_url is not None
        assert client.timeout is not None
    
    def test_client_custom_url(self):
        """Client accepts custom URL."""
        from services.api_gateway.clients.rag_service import RAGServiceClient
        
        client = RAGServiceClient(base_url="http://custom:9001")
        
        assert client.base_url == "http://custom:9001"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
