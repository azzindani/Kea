"""
Search MCP Server.

Provides web search tools via MCP protocol.
"""

from __future__ import annotations

import asyncio

from shared.mcp.server_base import MCPServer
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

from mcp_servers.search_server.tools.web_search import web_search_tool
from mcp_servers.search_server.tools.news_search import news_search_tool


logger = get_logger(__name__)


class SearchServer(MCPServer):
    """
    MCP Server for web search.
    
    Tools:
    - web_search: General web search
    - news_search: News-specific search
    """
    
    def __init__(self) -> None:
        super().__init__(name="search_server", version="1.0.0")
        self._register_tools()
    
    def _register_tools(self) -> None:
        """Register all search tools."""
        
        # web_search tool
        self.register_tool(
            name="web_search",
            description="Search the web using Tavily or Brave Search. Returns relevant URLs and snippets.",
            handler=self._handle_web_search,
            parameters={
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 10)"
                },
                "search_depth": {
                    "type": "string",
                    "description": "Search depth: basic or advanced (default: basic)"
                }
            },
            required=["query"]
        )
        
        # news_search tool
        self.register_tool(
            name="news_search",
            description="Search for news articles with date filtering.",
            handler=self._handle_news_search,
            parameters={
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "days": {
                    "type": "integer",
                    "description": "Search within last N days (default: 7)"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 10)"
                }
            },
            required=["query"]
        )
    
    async def _handle_web_search(self, arguments: dict) -> ToolResult:
        """Handle web_search tool call."""
        logger.info("Executing web search", extra={"query": arguments.get("query")})
        return await web_search_tool(arguments)
    
    async def _handle_news_search(self, arguments: dict) -> ToolResult:
        """Handle news_search tool call."""
        logger.info("Executing news search", extra={"query": arguments.get("query")})
        return await news_search_tool(arguments)


async def main() -> None:
    """Run the search server."""
    from shared.logging import setup_logging, LogConfig
    
    setup_logging(LogConfig(level="DEBUG", format="console", service_name="search_server"))
    
    server = SearchServer()
    logger.info(f"Starting {server.name} with {len(server.get_tools())} tools")
    
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
