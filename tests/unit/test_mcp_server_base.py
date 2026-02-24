"""
Tests for MCP server base class.
"""


import pytest
from shared.mcp.server_base import MCPServer, MCPServerBase

from shared.mcp.protocol import (
    JSONRPCRequest,
    MCPMethod,
    TextContent,
    ToolResult,
)


class ConcreteServer(MCPServer):
    """Concrete implementation for testing."""

    def __init__(self):
        super().__init__("test_server", "1.0.0")
        self.register_tool(
            name="test_tool",
            description="A test tool",
            handler=self.test_tool,
            parameters={"input": {"type": "string"}},
            required=["input"],
        )

    async def test_tool(self, arguments: dict) -> ToolResult:
        return ToolResult(
            content=[TextContent(text=f"Result: {arguments.get('input')}")],
        )


class TestMCPServer:
    """Tests for MCPServer base class."""

    @pytest.fixture
    def server(self):
        return ConcreteServer()

    def test_server_init(self, server):
        """Test server initialization."""
        assert server.name == "test_server"
        assert server.version == "1.0.0"

    def test_register_tool(self, server):
        """Test tool registration."""
        tools = server.get_tools()
        assert len(tools) == 1
        assert tools[0].name == "test_tool"
        assert tools[0].description == "A test tool"

    def test_get_tools(self, server):
        """Test getting registered tools."""
        tools = server.get_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

    @pytest.mark.asyncio
    async def test_handle_initialize(self, server):
        """Test handling initialize request."""
        request = JSONRPCRequest(
            id="1",
            method=MCPMethod.INITIALIZE.value,
            params={},
        )
        response = await server.handle_request(request)

        assert response.id == "1"
        assert response.error is None
        assert "capabilities" in response.result

    @pytest.mark.asyncio
    async def test_handle_tools_list(self, server):
        """Test handling tools/list request."""
        request = JSONRPCRequest(
            id="2",
            method=MCPMethod.TOOLS_LIST.value,
            params={},
        )
        response = await server.handle_request(request)

        assert response.id == "2"
        assert response.error is None
        assert "tools" in response.result
        assert len(response.result["tools"]) == 1

    @pytest.mark.asyncio
    async def test_handle_tool_call(self, server):
        """Test handling tools/call request."""
        request = JSONRPCRequest(
            id="3",
            method=MCPMethod.TOOLS_CALL.value,
            params={
                "name": "test_tool",
                "arguments": {"input": "hello"},
            },
        )
        response = await server.handle_request(request)

        assert response.id == "3"
        assert response.error is None
        assert response.result["content"][0]["text"] == "Result: hello"

    @pytest.mark.asyncio
    async def test_handle_tool_call_not_found(self, server):
        """Test handling tool call for non-existent tool."""
        request = JSONRPCRequest(
            id="4",
            method=MCPMethod.TOOLS_CALL.value,
            params={
                "name": "nonexistent_tool",
                "arguments": {},
            },
        )
        response = await server.handle_request(request)

        assert response.result["isError"] is True

    @pytest.mark.asyncio
    async def test_handle_ping(self, server):
        """Test handling ping request."""
        request = JSONRPCRequest(
            id="5",
            method=MCPMethod.PING.value,
            params={},
        )
        response = await server.handle_request(request)

        assert response.id == "5"
        assert response.error is None

    @pytest.mark.asyncio
    async def test_handle_unknown_method(self, server):
        """Test handling unknown method."""
        request = JSONRPCRequest(
            id="6",
            method="unknown/method",
            params={},
        )
        response = await server.handle_request(request)

        assert response.error is not None
        assert "not found" in response.error.message.lower()

    @pytest.mark.asyncio
    async def test_stop(self, server):
        """Test stopping server."""
        await server.stop()
        assert server._running is False


class TestMCPServerBase:
    """Tests for backward compatibility alias."""

    def test_alias_exists(self):
        """Test that MCPServerBase is an alias for MCPServer."""
        assert MCPServerBase is MCPServer
