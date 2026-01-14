"""
MCP Package - Model Context Protocol Implementation.

Provides:
- protocol: JSON-RPC 2.0 message types
- transport: stdio and SSE transport implementations
- server_base: Base class for MCP tool servers
- client_base: MCP client for connecting to servers
- tool_router: Semantic routing for 1000+ tools
"""

from shared.mcp.protocol import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
    JSONRPCNotification,
    MCPMethod,
    MCPErrorCode,
    Tool,
    ToolCallRequest,
    ToolResult,
    TextContent,
    ImageContent,
    InitializeRequest,
    InitializeResult,
    LogLevel,
    LogMessage,
)
from shared.mcp.tool_router import (
    ToolIndex,
    ToolRouter,
    ToolDescriptor,
    ToolCategory,
    get_tool_index,
    get_tool_router,
)

__all__ = [
    "JSONRPCRequest",
    "JSONRPCResponse",
    "JSONRPCError",
    "JSONRPCNotification",
    "MCPMethod",
    "MCPErrorCode",
    "Tool",
    "ToolCallRequest",
    "ToolResult",
    "TextContent",
    "ImageContent",
    "InitializeRequest",
    "InitializeResult",
    "LogLevel",
    "LogMessage",
    # Tool Router
    "ToolIndex",
    "ToolRouter",
    "ToolDescriptor",
    "ToolCategory",
    "get_tool_index",
    "get_tool_router",
]

