"""
MCP Server Base Class.

Provides the foundation for implementing MCP tool servers.
"""

from __future__ import annotations

import asyncio
import uuid
from abc import ABC
from typing import Any, Callable, Awaitable

from shared.mcp.protocol import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
    JSONRPCNotification,
    MCPMethod,
    MCPErrorCode,
    Tool,
    ToolInputSchema,
    ToolResult,
    TextContent,
    InitializeResult,
    ServerCapabilities,
)
from shared.mcp.transport import Transport, StdioTransport


# Type alias for tool handlers
ToolHandler = Callable[[dict[str, Any]], Awaitable[ToolResult]]


class MCPServer(ABC):
    """
    Base class for MCP tool servers.
    
    Subclass this to create a new MCP server with tools.
    
    Example:
        class ScraperServer(MCPServer):
            def __init__(self):
                super().__init__("scraper_server", "1.0.0")
                self.register_tool(
                    name="fetch_url",
                    description="Fetch URL content via HTTP",
                    handler=self.fetch_url,
                    parameters={"url": {"type": "string", "description": "URL to fetch"}}
                )
            
            async def fetch_url(self, arguments: dict) -> ToolResult:
                url = arguments["url"]
                # ... implementation
                return ToolResult(content=[TextContent(text=content)])
    """
    
    def __init__(self, name: str, version: str = "1.0.0") -> None:
        self.name = name
        self.version = version
        self._tools: dict[str, Tool] = {}
        self._handlers: dict[str, ToolHandler] = {}
        self._transport: Transport | None = None
        self._running = False
    
    def register_tool(
        self,
        name: str,
        description: str,
        handler: ToolHandler,
        parameters: dict[str, Any] | None = None,
        required: list[str] | None = None,
    ) -> None:
        """
        Register a tool with the server.
        
        Args:
            name: Tool name (unique identifier)
            description: Human-readable description
            handler: Async function that executes the tool
            parameters: JSON Schema properties for input
            required: List of required parameter names
        """
        schema = ToolInputSchema(
            properties=parameters or {},
            required=required or []
        )
        
        tool = Tool(
            name=name,
            description=description,
            inputSchema=schema
        )
        
        self._tools[name] = tool
        self._handlers[name] = handler
    
    def get_tools(self) -> list[Tool]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    async def handle_request(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """Handle an incoming JSON-RPC request."""
        
        try:
            if request.method == MCPMethod.INITIALIZE.value:
                result = await self._handle_initialize(request.params or {})
                return JSONRPCResponse(id=request.id, result=result.model_dump())
            
            elif request.method == MCPMethod.TOOLS_LIST.value:
                tools = [tool.model_dump() for tool in self.get_tools()]
                return JSONRPCResponse(id=request.id, result={"tools": tools})
            
            elif request.method == MCPMethod.TOOLS_CALL.value:
                result = await self._handle_tool_call(request.params or {})
                return JSONRPCResponse(id=request.id, result=result.model_dump())
            
            elif request.method == MCPMethod.PING.value:
                return JSONRPCResponse(id=request.id, result={})
            
            else:
                return JSONRPCResponse(
                    id=request.id,
                    error=JSONRPCError(
                        code=MCPErrorCode.METHOD_NOT_FOUND,
                        message=f"Method not found: {request.method}"
                    )
                )
        
        except Exception as e:
            return JSONRPCResponse(
                id=request.id,
                error=JSONRPCError(
                    code=MCPErrorCode.INTERNAL_ERROR,
                    message=str(e)
                )
            )
    
    async def _handle_initialize(self, params: dict) -> InitializeResult:
        """Handle initialization request."""
        return InitializeResult(
            capabilities=ServerCapabilities(
                tools={"listChanged": True}
            ),
            serverInfo={"name": self.name, "version": self.version}
        )
    
    async def _handle_tool_call(self, params: dict) -> ToolResult:
        """Handle tool call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self._handlers:
            return ToolResult(
                content=[TextContent(text=f"Tool not found: {tool_name}")],
                isError=True
            )
        
        try:
            handler = self._handlers[tool_name]
            return await handler(arguments)
        except Exception as e:
            return ToolResult(
                content=[TextContent(text=f"Tool execution error: {str(e)}")],
                isError=True
            )
    
    async def run(self, transport: Transport | None = None) -> None:
        """
        Run the MCP server.
        
        Args:
            transport: Transport to use (defaults to StdioTransport)
        """
        self._transport = transport or StdioTransport()
        
        if isinstance(self._transport, StdioTransport):
            await self._transport.start()
        
        self._running = True
        
        async for message in self._transport.receive():
            if not self._running:
                break
            
            # Parse and handle the request
            request = JSONRPCRequest(**message)
            response = await self.handle_request(request)
            await self._transport.send(response)
    
    async def stop(self) -> None:
        """Stop the server."""
        self._running = False
        if self._transport:
            await self._transport.close()
