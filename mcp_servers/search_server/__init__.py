# Search MCP Server Package
"""
Web search MCP server with multiple search engine integrations.

Tools:
- web_search: General web search
- news_search: News-specific search with date filtering
"""

from mcp_servers.search_server.server import SearchServer

__all__ = ["SearchServer"]
