"""
Unit Tests: Logging Metrics.

Tests for shared/logging/metrics.py
"""

import pytest


class TestMetrics:
    """Tests for Prometheus metrics."""
    
    def test_record_tool_call(self):
        """Record tool call metric."""
        from shared.logging.metrics import record_tool_call
        
        # Should not raise
        record_tool_call(
            tool_name="test_tool",
            server_name="test_server",
            duration=0.5,
            success=True,
        )
    
    def test_set_system_info(self):
        """Set system info metric."""
        from shared.logging.metrics import set_system_info
        
        # Should not raise
        set_system_info(version="1.0.0", environment="test")


class TestMiddleware:
    """Tests for logging middleware."""
    
    def test_request_logging_middleware(self):
        """Create request logging middleware."""
        from shared.logging.middleware import RequestLoggingMiddleware
        from fastapi import FastAPI
        
        app = FastAPI()
        
        # Should not raise
        app.add_middleware(RequestLoggingMiddleware)


class TestMCPMiddleware:
    """Tests for MCP logging middleware."""
    
    def test_create_middleware(self):
        """Create MCP middleware."""
        from shared.logging.mcp_middleware import MCPLoggingMiddleware
        
        middleware = MCPLoggingMiddleware(server_name="test")
        
        assert middleware.server_name == "test"
    
    def test_wrap_handler(self):
        """Wrap handler with logging."""
        from shared.logging.mcp_middleware import MCPLoggingMiddleware
        from shared.mcp.protocol import JSONRPCRequest, JSONRPCResponse
        
        middleware = MCPLoggingMiddleware(server_name="test")
        
        async def mock_handler(request: JSONRPCRequest) -> JSONRPCResponse:
            return JSONRPCResponse(jsonrpc="2.0", id=1, result={})
        
        wrapped = middleware.wrap(mock_handler)
        
        assert wrapped is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
