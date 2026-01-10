"""
MCP Protocol Types and Message Definitions.

Implements JSON-RPC 2.0 message types for Model Context Protocol communication.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JSONRPCVersion(str, Enum):
    """JSON-RPC version."""
    V2 = "2.0"


class MCPMethod(str, Enum):
    """MCP method names."""
    INITIALIZE = "initialize"
    INITIALIZED = "notifications/initialized"
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"
    LOGGING_SET_LEVEL = "logging/setLevel"
    PING = "ping"


# ============================================================================
# JSON-RPC Base Messages
# ============================================================================

class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 Request."""
    jsonrpc: JSONRPCVersion = JSONRPCVersion.V2
    id: str | int
    method: str
    params: dict[str, Any] | None = None


class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 Response."""
    jsonrpc: JSONRPCVersion = JSONRPCVersion.V2
    id: str | int
    result: Any | None = None
    error: JSONRPCError | None = None


class JSONRPCError(BaseModel):
    """JSON-RPC 2.0 Error."""
    code: int
    message: str
    data: Any | None = None


class JSONRPCNotification(BaseModel):
    """JSON-RPC 2.0 Notification (no id, no response expected)."""
    jsonrpc: JSONRPCVersion = JSONRPCVersion.V2
    method: str
    params: dict[str, Any] | None = None


# ============================================================================
# MCP Tool Types
# ============================================================================

class ToolInputSchema(BaseModel):
    """JSON Schema for tool input."""
    type: str = "object"
    properties: dict[str, Any] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)


class Tool(BaseModel):
    """MCP Tool definition."""
    name: str
    description: str
    inputSchema: ToolInputSchema


class ToolCallRequest(BaseModel):
    """Request to call a tool."""
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class TextContent(BaseModel):
    """Text content in tool result."""
    type: str = "text"
    text: str


class ImageContent(BaseModel):
    """Image content in tool result."""
    type: str = "image"
    data: str  # Base64 encoded
    mimeType: str = "image/png"


class ToolResult(BaseModel):
    """Result from tool execution."""
    content: list[TextContent | ImageContent]
    isError: bool = False


# ============================================================================
# MCP Initialization
# ============================================================================

class ClientCapabilities(BaseModel):
    """Client capabilities for initialization."""
    experimental: dict[str, Any] = Field(default_factory=dict)
    roots: dict[str, Any] = Field(default_factory=dict)
    sampling: dict[str, Any] = Field(default_factory=dict)


class ServerCapabilities(BaseModel):
    """Server capabilities returned during initialization."""
    experimental: dict[str, Any] = Field(default_factory=dict)
    logging: dict[str, Any] = Field(default_factory=dict)
    prompts: dict[str, Any] = Field(default_factory=dict)
    resources: dict[str, Any] = Field(default_factory=dict)
    tools: dict[str, Any] = Field(default_factory=dict)


class InitializeRequest(BaseModel):
    """Initialize request parameters."""
    protocolVersion: str = "2024-11-05"
    capabilities: ClientCapabilities = Field(default_factory=ClientCapabilities)
    clientInfo: dict[str, str] = Field(default_factory=lambda: {"name": "research-engine", "version": "0.1.0"})


class InitializeResult(BaseModel):
    """Initialize response result."""
    protocolVersion: str = "2024-11-05"
    capabilities: ServerCapabilities = Field(default_factory=ServerCapabilities)
    serverInfo: dict[str, str] = Field(default_factory=dict)


# ============================================================================
# MCP Progress and Logging
# ============================================================================

class ProgressToken(BaseModel):
    """Progress notification token."""
    token: str | int
    progress: float
    total: float | None = None


class LogLevel(str, Enum):
    """Log levels for MCP logging."""
    DEBUG = "debug"
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    ALERT = "alert"
    EMERGENCY = "emergency"


class LogMessage(BaseModel):
    """MCP log message."""
    level: LogLevel
    logger: str | None = None
    data: Any = None


# ============================================================================
# Error Codes
# ============================================================================

class MCPErrorCode:
    """Standard JSON-RPC and MCP error codes."""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # MCP-specific errors
    TOOL_NOT_FOUND = -32001
    RESOURCE_NOT_FOUND = -32002
    EXECUTION_ERROR = -32003
