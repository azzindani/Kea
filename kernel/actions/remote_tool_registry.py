"""
Remote Tool Registry Implementation.

Connects to the MCP Host service via HTTP to provide tool schemas and execution
capabilities to the Kernel, respecting the microservices architecture.
"""
from __future__ import annotations

import httpx
from typing import Any, Dict, List, Optional

from kernel.interfaces.tool_registry import ToolRegistry
from shared.service_registry import ServiceName, ServiceRegistry
from shared.logging import get_logger

logger = get_logger(__name__)


class RemoteToolRegistry:
    """
    Client-side implementation of ToolRegistry that talks to MCP Host.
    """

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self._schema_cache: Dict[str, Dict[str, Any]] = {}

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools from MCP Host."""
        try:
            url = ServiceRegistry.get_url(ServiceName.MCP_HOST)
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(f"{url}/tools")
                if resp.status_code == 200:
                    data = resp.json()
                    tools = data.get("tools", [])
                    # Cache schemas while we have them
                    for t in tools:
                        if "name" in t and "inputSchema" in t:
                            self._schema_cache[t["name"]] = t["inputSchema"]
                    return tools
        except Exception as e:
            logger.error(f"RemoteToolRegistry list_tools failed: {e}")
        return []

    async def search_tools(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search tools using MCP Host's RAG search."""
        try:
            url = ServiceRegistry.get_url(ServiceName.MCP_HOST)
            payload = {"query": query, "limit": limit}
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{url}/tools/search", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    tools = data.get("tools", [])
                    return tools
        except Exception as e:
            logger.error(f"RemoteToolRegistry search_tools failed: {e}")
        return []

    async def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get schema for a specific tool."""
        # Check cache first
        if tool_name in self._schema_cache:
            return self._schema_cache[tool_name]

        # Fetch fresh list if missing (could be a new tool)
        # Optimization: We could add a specific GET /tools/{name} endpoint to MCP Host later
        # For now, refreshing the list is the standard way to sync.
        await self.list_tools()
        
        return self._schema_cache.get(tool_name)

    def get_server_for_tool(self, tool_name: str) -> Optional[str]:
        """
        Get server name. 
        Note: Remote clients don't strictly need to know the server name 
        as MCP Host handles routing, but we can try to guess or fetch it.
        """
        # Remote registry doesn't track server mapping closely, returns None
        # forcing logic to rely on tool name uniquity or MCP Host routing.
        return None

    async def execute_tool(self, tool_name: str, arguments: dict) -> Any:
        """Execute tool via MCP Host."""
        try:
            url = ServiceRegistry.get_url(ServiceName.MCP_HOST)
            async with httpx.AsyncClient(timeout=self.timeout * 2) as client:
                resp = await client.post(
                    f"{url}/tools/execute",
                    json={"tool_name": tool_name, "arguments": arguments},
                )
                if resp.status_code == 200:
                    return resp.json()
                else:
                    logger.error(f"Tool execution failed {resp.status_code}: {resp.text}")
                    from shared.mcp.protocol import ToolResult, TextContent
                    return ToolResult(
                        content=[TextContent(text=f"Error: {resp.text}")],
                        isError=True
                    )
        except Exception as e:
            logger.error(f"RemoteToolRegistry execute_tool failed: {e}")
            from shared.mcp.protocol import ToolResult, TextContent
            return ToolResult(
                content=[TextContent(text=f"Exception: {str(e)}")],
                isError=True
            )
