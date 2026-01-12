"""
Orchestrator Service Client.

HTTP client for calling the Orchestrator service.
"""

from __future__ import annotations

from typing import Any, AsyncIterator
import httpx

from shared.logging import get_logger
from shared.config import get_settings

logger = get_logger(__name__)


class OrchestratorClient:
    """
    HTTP client for the Orchestrator service.
    
    Features:
    - Synchronous research requests
    - Streaming research with SSE
    - Tool invocation
    - Health checks
    
    Example:
        client = OrchestratorClient()
        result = await client.start_research("What is AI?", depth=2)
    """
    
    def __init__(self, base_url: str | None = None) -> None:
        settings = get_settings()
        self.base_url = base_url or f"http://localhost:{settings.api_port}"
        self.timeout = httpx.Timeout(120.0, connect=10.0)
    
    async def health_check(self) -> dict[str, Any]:
        """Check orchestrator health."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
    
    async def list_tools(self) -> list[dict[str, Any]]:
        """Get list of available MCP tools."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/tools")
            response.raise_for_status()
            return response.json().get("tools", [])
    
    async def start_research(
        self,
        query: str,
        depth: int = 2,
        max_sources: int = 10,
    ) -> dict[str, Any]:
        """
        Start a synchronous research job.
        
        Args:
            query: Research query
            depth: Research depth (1-5)
            max_sources: Max sources to use
            
        Returns:
            Research result with report, confidence, etc.
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/research",
                json={
                    "query": query,
                    "depth": depth,
                    "max_sources": max_sources,
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def stream_research(
        self,
        query: str,
        depth: int = 2,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Stream research results via SSE.
        
        Args:
            query: Research query
            depth: Research depth
            
        Yields:
            Event dicts with type and data
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "GET",
                f"{self.base_url}/research/stream",
                params={"query": query, "depth": depth},
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    
                    import json
                    try:
                        data = json.loads(line[6:])
                        yield data
                    except json.JSONDecodeError:
                        continue
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Call an MCP tool directly.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/tools/{tool_name}",
                json=arguments,
            )
            response.raise_for_status()
            return response.json()
