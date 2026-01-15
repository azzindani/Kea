"""
Unit Tests: MCP Server Base.

Tests for MCP server base class.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from shared.mcp.server_base import (
    MCPServerBase,
    ToolDefinition,
    ToolResult,
)


class TestToolDefinition:
    """Test ToolDefinition dataclass."""
    
    def test_create_tool_definition(self):
        """Test tool definition creation."""
        tool = ToolDefinition(
            name="web_search",
            description="Search the web",
            parameters={
                "query": {"type": "string", "required": True},
            },
        )
        
        assert tool.name == "web_search"
        assert tool.description == "Search the web"
    
    def test_to_schema(self):
        """Test conversion to JSON schema."""
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            parameters={"param1": {"type": "string"}},
        )
        
        schema = tool.to_schema()
        
        assert schema["name"] == "test_tool"
        assert "inputSchema" in schema


class TestToolResult:
    """Test ToolResult dataclass."""
    
    def test_success_result(self):
        """Test successful tool result."""
        result = ToolResult(
            success=True,
            data={"key": "value"},
        )
        
        assert result.success is True
        assert result.data["key"] == "value"
    
    def test_error_result(self):
        """Test error tool result."""
        result = ToolResult(
            success=False,
            error="Something went wrong",
        )
        
        assert result.success is False
        assert result.error == "Something went wrong"
    
    def test_to_content(self):
        """Test conversion to MCP content format."""
        result = ToolResult(
            success=True,
            data={"message": "Hello"},
        )
        
        content = result.to_content()
        
        assert isinstance(content, list)


class TestMCPServerBase:
    """Test MCPServerBase class."""
    
    def test_server_init(self):
        """Test server initialization."""
        server = MCPServerBase(name="test_server")
        
        assert server.name == "test_server"
    
    def test_register_tool(self):
        """Test registering a tool."""
        server = MCPServerBase(name="test_server")
        
        @server.tool("my_tool", "A test tool")
        async def my_tool(param1: str):
            return {"result": param1}
        
        assert "my_tool" in server._tools
    
    def test_list_tools(self):
        """Test listing registered tools."""
        server = MCPServerBase(name="test_server")
        
        @server.tool("tool1", "First tool")
        async def tool1():
            pass
        
        @server.tool("tool2", "Second tool")
        async def tool2():
            pass
        
        tools = server.list_tools()
        
        assert len(tools) == 2
    
    @pytest.mark.asyncio
    async def test_call_tool(self):
        """Test calling a registered tool."""
        server = MCPServerBase(name="test_server")
        
        @server.tool("echo", "Echo input")
        async def echo(message: str):
            return {"echoed": message}
        
        result = await server.call_tool("echo", {"message": "hello"})
        
        assert result["echoed"] == "hello"
    
    @pytest.mark.asyncio
    async def test_call_unknown_tool(self):
        """Test calling unknown tool raises error."""
        server = MCPServerBase(name="test_server")
        
        with pytest.raises(ValueError):
            await server.call_tool("unknown", {})
