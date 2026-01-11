"""
Orchestrator MCP Client.

Manages connections to MCP tool servers and provides parallel execution.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any

from shared.mcp.client import MCPClient
from shared.mcp.protocol import Tool, ToolResult, TextContent
from shared.mcp.transport import StdioTransport
from shared.logging import get_logger
from shared.logging.metrics import record_tool_call, ACTIVE_TOOLS


logger = get_logger(__name__)


@dataclass
class MCPServerConnection:
    """Connection to an MCP server."""
    name: str
    command: str
    client: MCPClient | None = None
    process: subprocess.Popen | None = None
    tools: list[Tool] = field(default_factory=list)
    is_connected: bool = False


class MCPOrchestrator:
    """
    Orchestrates connections to multiple MCP servers.
    
    Features:
    - Start/stop MCP server processes
    - Discover tools from all servers
    - Execute tools in parallel
    - Track metrics
    
    Example:
        orchestrator = MCPOrchestrator()
        await orchestrator.start_servers([
            {"name": "scraper", "command": "python -m mcp_servers.scraper_server.server"},
            {"name": "python", "command": "python -m mcp_servers.python_server.server"},
        ])
        
        result = await orchestrator.call_tool("fetch_url", {"url": "https://example.com"})
    """
    
    def __init__(self) -> None:
        self._servers: dict[str, MCPServerConnection] = {}
        self._tool_registry: dict[str, str] = {}  # tool_name -> server_name
    
    @property
    def tools(self) -> list[Tool]:
        """Get all available tools from all servers."""
        all_tools = []
        for server in self._servers.values():
            all_tools.extend(server.tools)
        return all_tools
    
    @property
    def tool_names(self) -> list[str]:
        """Get all tool names."""
        return list(self._tool_registry.keys())
    
    async def start_servers(self, server_configs: list[dict]) -> None:
        """
        Start MCP servers and discover their tools.
        
        Args:
            server_configs: List of {"name": str, "command": str}
        """
        for config in server_configs:
            name = config["name"]
            command = config["command"]
            
            logger.info(f"Starting MCP server: {name}")
            
            try:
                connection = MCPServerConnection(name=name, command=command)
                
                # Start the server process
                process = subprocess.Popen(
                    command.split(),
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                connection.process = process
                
                # Create transport and client
                # Note: In production, we'd use the process's stdin/stdout
                # For now, we'll use a simplified approach
                
                # TODO: Implement proper stdio transport with subprocess
                # For now, mark as connected and register known tools
                connection.is_connected = True
                self._servers[name] = connection
                
                logger.info(f"Started MCP server: {name}")
                
            except Exception as e:
                logger.error(f"Failed to start {name}: {e}")
    
    async def discover_tools(self) -> list[Tool]:
        """Discover tools from all connected servers."""
        all_tools = []
        
        for name, server in self._servers.items():
            if server.client and server.is_connected:
                try:
                    tools = await server.client.list_tools()
                    server.tools = tools
                    
                    for tool in tools:
                        self._tool_registry[tool.name] = name
                        all_tools.append(tool)
                    
                    logger.info(f"Discovered {len(tools)} tools from {name}")
                    
                except Exception as e:
                    logger.error(f"Failed to discover tools from {name}: {e}")
        
        return all_tools
    
    def get_tool_server(self, tool_name: str) -> str | None:
        """Get the server name for a tool."""
        return self._tool_registry.get(tool_name)
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> ToolResult:
        """
        Call a tool by name with retry support.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            ToolResult with content
        """
        server_name = self._tool_registry.get(tool_name)
        
        if not server_name:
            return ToolResult(
                content=[TextContent(text=f"Tool not found: {tool_name}")],
                isError=True
            )
        
        server = self._servers.get(server_name)
        if not server or not server.client:
            return ToolResult(
                content=[TextContent(text=f"Server not available: {server_name}")],
                isError=True
            )
        
        # Get retry config
        from shared.config import get_settings
        settings = get_settings()
        max_retries = settings.mcp.max_retries
        retry_delay = settings.mcp.retry_delay
        retry_backoff = settings.mcp.retry_backoff
        
        last_error = None
        
        for attempt in range(max_retries):
            import time
            start_time = time.perf_counter()
            
            try:
                ACTIVE_TOOLS.labels(server_name=server_name).inc()
                
                result = await server.client.call_tool(tool_name, arguments)
                
                duration = time.perf_counter() - start_time
                record_tool_call(tool_name, server_name, duration, not result.isError)
                
                return result
                
            except asyncio.TimeoutError as e:
                last_error = e
                if settings.mcp.retry_on_timeout and attempt < max_retries - 1:
                    wait_time = retry_delay * (retry_backoff ** attempt)
                    logger.warning(f"Tool {tool_name} timeout, retry {attempt + 1}/{max_retries} in {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                    continue
                raise
                
            except (ConnectionError, OSError) as e:
                last_error = e
                if settings.mcp.retry_on_connection_error and attempt < max_retries - 1:
                    wait_time = retry_delay * (retry_backoff ** attempt)
                    logger.warning(f"Tool {tool_name} connection error, retry {attempt + 1}/{max_retries} in {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                    continue
                raise
                
            except Exception as e:
                logger.error(f"Tool {tool_name} error: {e}")
                return ToolResult(
                    content=[TextContent(text=f"Error: {str(e)}")],
                    isError=True
                )
                
            finally:
                ACTIVE_TOOLS.labels(server_name=server_name).dec()
        
        # All retries exhausted
        return ToolResult(
            content=[TextContent(text=f"Failed after {max_retries} attempts: {last_error}")],
            isError=True
        )
    
    async def call_tools_parallel(
        self,
        calls: list[tuple[str, dict[str, Any]]],
    ) -> list[ToolResult]:
        """
        Execute multiple tool calls in parallel.
        
        Args:
            calls: List of (tool_name, arguments) tuples
            
        Returns:
            List of ToolResults in same order as calls
        """
        tasks = [
            self.call_tool(tool_name, arguments)
            for tool_name, arguments in calls
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        final_results = []
        for result in results:
            if isinstance(result, Exception):
                final_results.append(ToolResult(
                    content=[TextContent(text=f"Error: {str(result)}")],
                    isError=True
                ))
            else:
                final_results.append(result)
        
        return final_results
    
    async def stop_servers(self) -> None:
        """Stop all MCP server processes."""
        for name, server in self._servers.items():
            try:
                if server.client:
                    await server.client.close()
                
                if server.process:
                    server.process.terminate()
                    server.process.wait(timeout=5)
                
                server.is_connected = False
                logger.info(f"Stopped MCP server: {name}")
                
            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")
        
        self._servers.clear()
        self._tool_registry.clear()
