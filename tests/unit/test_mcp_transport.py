"""
Unit Tests: MCP Transport Layer.

Tests for MCP transport and tool router.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from shared.mcp.transport import (
    MCPTransport,
    TransportConfig,
)
from shared.mcp.tool_router import (
    ToolRouter,
    RouteConfig,
)


class TestTransportConfig:
    """Test TransportConfig dataclass."""
    
    def test_default_config(self):
        """Test default transport config."""
        config = TransportConfig()
        
        assert config.timeout >= 0
        assert config.max_retries >= 0
    
    def test_custom_config(self):
        """Test custom transport config."""
        config = TransportConfig(
            timeout=60.0,
            max_retries=5,
        )
        
        assert config.timeout == 60.0
        assert config.max_retries == 5


class TestMCPTransport:
    """Test MCPTransport class."""
    
    @pytest.fixture
    def transport(self):
        """Create transport for testing."""
        return MCPTransport()
    
    def test_transport_init(self, transport):
        """Test transport initialization."""
        assert transport is not None
    
    @pytest.mark.asyncio
    async def test_send_request(self, transport):
        """Test sending MCP request."""
        with patch.object(transport, "_client") as mock:
            mock.post = AsyncMock(return_value=MagicMock(
                status_code=200,
                json=lambda: {"result": "success"},
            ))
            
            result = await transport.send(
                method="tools/list",
                params={},
            )
            
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_send_with_retry(self, transport):
        """Test retry on failure."""
        call_count = 0
        
        async def failing_then_success(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Failed")
            return MagicMock(status_code=200, json=lambda: {})
        
        with patch.object(transport, "_client") as mock:
            mock.post = failing_then_success
            
            await transport.send(method="test", params={})
            
            assert call_count >= 2


class TestRouteConfig:
    """Test RouteConfig dataclass."""
    
    def test_default_route(self):
        """Test default route config."""
        config = RouteConfig(
            tool_name="web_search",
            server_name="search_server",
        )
        
        assert config.tool_name == "web_search"
        assert config.server_name == "search_server"


class TestToolRouter:
    """Test ToolRouter class."""
    
    @pytest.fixture
    def router(self):
        """Create router for testing."""
        return ToolRouter()
    
    def test_router_init(self, router):
        """Test router initialization."""
        assert router._routes == {} or isinstance(router._routes, dict)
    
    def test_register_route(self, router):
        """Test registering a route."""
        router.register(
            tool_name="web_search",
            server_name="search_server",
        )
        
        assert "web_search" in router._routes
    
    def test_get_server_for_tool(self, router):
        """Test getting server for tool."""
        router.register("web_search", "search_server")
        
        server = router.get_server("web_search")
        
        assert server == "search_server"
    
    def test_get_server_unknown_tool(self, router):
        """Test getting unknown tool returns None."""
        server = router.get_server("unknown_tool")
        
        assert server is None
    
    def test_list_routes(self, router):
        """Test listing all routes."""
        router.register("tool1", "server1")
        router.register("tool2", "server2")
        
        routes = router.list_routes()
        
        assert len(routes) == 2
