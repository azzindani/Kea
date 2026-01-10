"""
Unit Tests: MCP Client.

Tests for shared/mcp/client.py and transport.py
"""

import pytest


class TestMCPClient:
    """Tests for MCP client."""
    
    def test_init(self):
        """Initialize client."""
        from shared.mcp.client import MCPClient
        
        client = MCPClient(server_name="test_server")
        
        assert client.server_name == "test_server"
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """List available tools."""
        from shared.mcp.client import MCPClient
        
        client = MCPClient(server_name="test")
        
        # Should not raise even without connection
        tools = await client.list_tools()
        
        assert isinstance(tools, list)


class TestServerBase:
    """Tests for MCP server base class."""
    
    def test_init(self):
        """Initialize server base."""
        from shared.mcp.server_base import MCPServerBase
        
        class TestServer(MCPServerBase):
            def get_tools(self):
                return []
            
            async def handle_tool_call(self, name, args):
                return {"result": "ok"}
        
        server = TestServer(name="test_server")
        
        assert server.name == "test_server"


class TestTransport:
    """Tests for MCP transport."""
    
    def test_stdio_transport(self):
        """Create stdio transport."""
        from shared.mcp.transport import StdioTransport
        
        transport = StdioTransport()
        
        assert transport is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
