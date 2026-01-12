# Browser Agent MCP Server
"""
Intelligent browsing agent for human-like research.
"""

from mcp_servers.browser_agent_server.server import (
    BrowserAgentServer,
    human_like_search_tool,
    source_validator_tool,
)

__all__ = [
    "BrowserAgentServer",
    "human_like_search_tool",
    "source_validator_tool",
]
