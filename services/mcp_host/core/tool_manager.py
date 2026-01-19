"""
Orchestrator MCP Client.

Manages connections to MCP tool servers and provides parallel execution.

Integrates with:
- recovery.py: Centralized retry and circuit breaker
- jit_loader.py: Auto-install dependencies before server start
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
from services.orchestrator.core.recovery import (
    retry,
    CircuitBreaker,
    CircuitOpenError,
    get_circuit_breaker,
)


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
    
    
    # Singleton instance
    _instance: MCPOrchestrator | None = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MCPOrchestrator, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
            
        self._servers: dict[str, MCPServerConnection] = {}
        self._tool_registry: dict[str, str] = {}  # tool_name -> server_name
        self._initialized = True
    
    @classmethod
    def get_instance(cls) -> MCPOrchestrator:
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = MCPOrchestrator()
        return cls._instance
        
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
        from shared.mcp.client import MCPClient
        from shared.mcp.transport import SubprocessTransport
        
        for config in server_configs:
            name = config["name"]
            command = config["command"]
            
            logger.info(f"Starting MCP server: {name} (cmd: {command})")
            
            try:
                # Use asyncio.create_subprocess_shell for Async pipes
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                # Check for immediate failure
                try:
                    await asyncio.wait_for(process.wait(), timeout=0.5)
                    if process.returncode is not None:
                        # Capture stderr
                        err = await process.stderr.read()
                        logger.error(f"❌ Server {name} failed immediately (code {process.returncode}): {err.decode()}")
                        continue
                except asyncio.TimeoutError:
                    # Process is running, good.
                    pass
                
                # Create Transport & Client
                transport = SubprocessTransport(process)
                client = MCPClient()
                
                # Connect (Initialize handshake)
                logger.info(f"🔌 Connecting to {name} via stdio...")
                await client.connect(transport)
                
                connection = MCPServerConnection(
                    name=name, 
                    command=command,
                    client=client,
                    process=process,
                    is_connected=True
                )
                self._servers[name] = connection
                
                # Initial Discovery
                tools = await client.list_tools()
                connection.tools = tools
                
                for tool in tools:
                    self._tool_registry[tool.name] = name
                    
                logger.info(f"✅ Connected to {name}: Discovered {len(tools)} tools")
                
            except Exception as e:
                logger.error(f"❌ Failed to start/connect {name}: {e}")
                
        # Update Registry
        try:
            from services.mcp_host.core.tool_registry import get_tool_registry
            registry = get_tool_registry()
            await registry.sync_tools(self.tools)
        except Exception as e:
            logger.error(f"Failed to sync tool registry: {e}")
    
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
        Call a tool by name with automatic retry and circuit breaker.
        
        Uses centralized recovery.py for:
        - Exponential backoff retry
        - Error classification
        - Circuit breaker protection
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            ToolResult with content
        """
        # =====================================================================
        # Enterprise Guardrail: Compliance Check
        # =====================================================================
        try:
            from shared.service_registry import ServiceRegistry, ServiceName
            import httpx
            
            swarm_url = ServiceRegistry.get_url(ServiceName.SWARM_MANAGER)
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    f"{swarm_url}/compliance/check",
                    json={
                        "operation": "tool_exec",
                        "context": {"tool": tool_name, "args": arguments}
                    }
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    if not data.get("passed", True):
                        logger.warning(f"🛡️ Compliance blocked {tool_name}: {data.get('summary')}")
                        issues_text = "\n".join([f"- {i.get('message')}" for i in data.get("issues", [])])
                        return ToolResult(
                            content=[TextContent(text=f"Compliance Blocked Action:\n{issues_text}")],
                            isError=True
                        )
                else:
                    logger.warning(f"Compliance check returned {resp.status_code}, allowing tool call (Fail Open)")

        except ImportError:
            pass
        except Exception as e:
            logger.error(f"Compliance check failed: {e}")
            # Decide: Fail open or closed? Currently Fail Open to avoid breaking production
        # =====================================================================

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
        
        # Get circuit breaker for this server
        breaker = get_circuit_breaker(f"mcp_{server_name}")
        
        return await self._call_tool_with_recovery(
            server, server_name, tool_name, arguments, breaker
        )
    
    @retry(max_attempts=3, base_delay=1.0, max_delay=30.0)
    async def _call_tool_with_recovery(
        self,
        server: MCPServerConnection,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any],
        breaker: CircuitBreaker,
    ) -> ToolResult:
        """Execute tool call with retry decorator and circuit breaker."""
        import time
        start_time = time.perf_counter()
        
        try:
            # Check circuit breaker
            async with breaker:
                ACTIVE_TOOLS.labels(server_name=server_name).inc()
                try:
                    result = await server.client.call_tool(tool_name, arguments)
                    
                    duration = time.perf_counter() - start_time
                    record_tool_call(tool_name, server_name, duration, not result.isError)
                    
                    return result
                finally:
                    ACTIVE_TOOLS.labels(server_name=server_name).dec()
                    
        except CircuitOpenError as e:
            logger.warning(f"Circuit breaker open for {server_name}: {e}")
            return ToolResult(
                content=[TextContent(text=f"Server temporarily unavailable: {server_name}")],
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
        """
        Stop all MCP server processes.
        
        Prioritizes graceful termination, falls back to kill.
        """
        for name, server in self._servers.items():
            try:
                if server.client:
                    # Best effort to close client
                    try:
                        await asyncio.wait_for(server.client.close(), timeout=2.0)
                    except Exception:
                        pass
                
                if server.process:
                    # Graceful terminate
                    server.process.terminate()
                    try:
                        await asyncio.wait_for(server.process.wait(), timeout=5)
                        logger.info(f"Gracefully stopped MCP server: {name}")
                    except asyncio.TimeoutError:
                        # Force kill
                        logger.warning(f"Force killing hung server: {name}")
                        server.process.kill()
                        server.process.wait()
                
                server.is_connected = False
                
            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")
        
        self._servers.clear()
        self._tool_registry.clear()


# ============================================================================
# Singleton Accessor
# ============================================================================

_orchestrator_instance: MCPOrchestrator | None = None


def get_mcp_orchestrator() -> MCPOrchestrator:
    """
    Get or create global MCP orchestrator instance.
    
    Returns:
        MCPOrchestrator instance
    """
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = MCPOrchestrator()
    return _orchestrator_instance
