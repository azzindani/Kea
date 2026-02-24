"""
Unit Tests: MCP Client.

Tests for shared/mcp/client.py
"""

import pytest


class TestMCPClient:
    """Tests for MCP client."""

    def test_init(self):
        """Initialize MCP client."""
        from shared.mcp.client import MCPClient

        client = MCPClient()

        assert client is not None
        assert client._initialized == False

    def test_list_tools(self):
        """Client has list_tools method."""
        from shared.mcp.client import MCPClient

        client = MCPClient()

        # Verify method exists
        assert hasattr(client, "list_tools")
        assert callable(client.list_tools)


class TestServerBase:
    """Tests for MCP server base."""

    def test_init(self):
        """Initialize MCP server."""
        from shared.mcp.server_base import MCPServer

        class TestServer(MCPServer):
            pass

        server = TestServer("test_server", "1.0.0")

        assert server.name == "test_server"
        assert server.version == "1.0.0"


class TestTransport:
    """Tests for MCP transport."""

    def test_stdio_transport(self):
        """Create stdio transport."""
        from shared.mcp.transport import StdioTransport

        transport = StdioTransport()

        assert transport is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
