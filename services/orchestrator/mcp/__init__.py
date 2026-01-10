# Orchestrator MCP package
"""
MCP client integration for the orchestrator.

- client: Multi-server MCP orchestrator
- registry: Tool discovery and registration
"""

from services.orchestrator.mcp.client import MCPOrchestrator

__all__ = ["MCPOrchestrator"]
