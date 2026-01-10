"""
MCP Package - Model Context Protocol Implementation.

Provides:
- protocol: JSON-RPC 2.0 message types
- transport: stdio and SSE transport implementations
- server_base: Base class for MCP tool servers
- client_base: MCP client for connecting to servers
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
]
