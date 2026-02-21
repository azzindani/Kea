"""
MCP Service Client.

HTTP client for calling the MCP Host service.
Standardized for v0.4.0 JIT architecture.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

import httpx

from shared.logging.main import get_logger
from shared.config import get_settings
from shared.service_registry import ServiceRegistry, ServiceName


logger = get_logger(__name__)


class MCPClient:
    """
    HTTP client for the MCP Host service.
    
    Features:
    - Tool discovery
    - RAG-based tool search
    - JIT tool execution
    """
    
    def __init__(self, base_url: str | None = None) -> None:
        settings = get_settings()
        self.base_url = base_url or ServiceRegistry.get_url(ServiceName.MCP_HOST)
        self.timeout = httpx.Timeout(
            settings.timeouts.default,
            connect=settings.timeouts.auth_token,
        )
        self._client: httpx.AsyncClient | None = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def health_check(self) -> dict[str, Any]:
        """Check MCP host health."""
        client = await self._get_client()
        response = await client.get("/health")
        response.raise_for_status()
        return response.json()
    
    async def list_tools(self) -> list[dict[str, Any]]:
        """List all available tools."""
        client = await self._get_client()
        response = await client.get("/tools")
        response.raise_for_status()
        return response.json().get("tools", [])
    
    async def search_tools(self, query: str, limit: int | None = None) -> list[dict[str, Any]]:
        """Search for tools using RAG."""
        settings = get_settings()
        limit = limit or settings.api.default_limit
        
        client = await self._get_client()
        response = await client.post(
            "/tools/search",
            json={"query": query, "limit": limit},
        )
        response.raise_for_status()
        return response.json().get("tools", [])
    
    async def invoke(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Invoke an MCP tool.
        
        Args:
            tool_name: Full name of the tool (e.g. "google_search")
            arguments: Tool arguments
            
        Returns:
            Tool output from MCP Host
        """
        client = await self._get_client()
        response = await client.post(
            "/tools/execute",
            json={"tool_name": tool_name, "arguments": arguments},
        )
        # We don't raise_for_status here because we want to return the Error response
        return response.json()


# Singleton
_client: Optional[MCPClient] = None

async def get_mcp_client() -> MCPClient:
    """Get singleton client."""
    global _client
    if _client is None:
        _client = MCPClient()
    return _client
