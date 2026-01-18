"""
MCP Client Implementation.

Provides client-side connection to MCP servers for tool invocation.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from shared.mcp.protocol import (
    JSONRPCRequest,
    JSONRPCResponse,
    MCPMethod,
    Tool,
    ToolResult,
    TextContent,
    InitializeRequest,
)
from shared.mcp.transport import Transport, StdioTransport


class MCPClient:
    """
    Client for connecting to MCP servers.
    
    Example:
        client = MCPClient()
        await client.connect(transport)
        
        tools = await client.list_tools()
        result = await client.call_tool("fetch_url", {"url": "https://example.com"})
    """
    
    def __init__(self) -> None:
        self._transport: Transport | None = None
        self._pending: dict[str | int, asyncio.Future[JSONRPCResponse]] = {}
        self._tools: list[Tool] = []
        self._initialized = False
        self._receive_task: asyncio.Task | None = None
    
    async def connect(self, transport: Transport) -> None:
        """
        Connect to an MCP server via the given transport.
        
        Args:
            transport: Transport instance (StdioTransport or SSETransport)
        """
        self._transport = transport
        
        if isinstance(transport, StdioTransport):
            await transport.start()
        
        # Start receiving messages
        self._receive_task = asyncio.create_task(self._receive_loop())
        
        # Initialize the connection
        await self._initialize()
    
    async def _initialize(self) -> None:
        """Send initialization request."""
        request = InitializeRequest()
        response = await self._send_request(MCPMethod.INITIALIZE.value, request.model_dump())
        
        if response.error:
            raise RuntimeError(f"Initialization failed: {response.error.message}")
        
        self._initialized = True
    
    async def _receive_loop(self) -> None:
        """Background task to receive and dispatch responses."""
        if not self._transport:
            return
        
        async for message in self._transport.receive():
            response = JSONRPCResponse(**message)
            
            if response.id in self._pending:
                future = self._pending.pop(response.id)
                future.set_result(response)
    
    async def _send_request(self, method: str, params: dict[str, Any] | None = None) -> JSONRPCResponse:
        """Send a request and wait for response."""
        if not self._transport:
            raise RuntimeError("Not connected")
        
        request_id = str(uuid.uuid4())
        request = JSONRPCRequest(id=request_id, method=method, params=params)
        
        # Create future for response
        future: asyncio.Future[JSONRPCResponse] = asyncio.Future()
        self._pending[request_id] = future
        
        # Send request
        await self._transport.send(request)
        
        # Wait for response with timeout
        try:
            # Increase timeout to 300s for JIT installations
            return await asyncio.wait_for(future, timeout=300.0)
        except asyncio.TimeoutError:
            self._pending.pop(request_id, None)
            raise TimeoutError(f"Request timed out: {method}")
    
    async def list_tools(self) -> list[Tool]:
        """
        Get list of available tools from the server.
        
        Returns:
            List of Tool objects
        """
        response = await self._send_request(MCPMethod.TOOLS_LIST.value)
        
        if response.error:
            raise RuntimeError(f"Failed to list tools: {response.error.message}")
        
        tools_data = response.result.get("tools", [])
        self._tools = [Tool(**t) for t in tools_data]
        return self._tools
    
    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> ToolResult:
        """
        Call a tool on the server.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            ToolResult with content
        """
        response = await self._send_request(
            MCPMethod.TOOLS_CALL.value,
            {"name": name, "arguments": arguments or {}}
        )
        
        if response.error:
            return ToolResult(
                content=[TextContent(text=f"Error: {response.error.message}")],
                isError=True
            )
        
        return ToolResult(**response.result)
    
    async def ping(self) -> bool:
        """Ping the server to check connectivity."""
        try:
            response = await self._send_request(MCPMethod.PING.value)
            return response.error is None
        except Exception:
            return False
    
    async def close(self) -> None:
        """Close the connection."""
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        
        if self._transport:
            await self._transport.close()
