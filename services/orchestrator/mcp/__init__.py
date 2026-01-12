# Orchestrator MCP Package
"""
MCP client and tool management for the orchestrator.

Components:
- client: MCPOrchestrator for managing MCP servers
- registry: Tool discovery and registration
- parallel_executor: Concurrent tool execution
"""

from services.orchestrator.mcp.client import MCPOrchestrator
from services.orchestrator.mcp.registry import ToolRegistry, get_registry
from services.orchestrator.mcp.parallel_executor import ParallelExecutor, execute_tools_parallel

__all__ = [
    "MCPOrchestrator",
    "ToolRegistry",
    "get_registry",
    "ParallelExecutor",
    "execute_tools_parallel",
]
