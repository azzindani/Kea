# /// script
# dependencies = [
#   "mcp",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import web_search, news_search
import structlog

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("search_server")

@mcp.tool()
async def web_search(query: str, max_results: int = 10, search_depth: str = "basic") -> str:
    """Search the web using Tavily or Brave Search.
    Args:
        query: Search query
        max_results: Maximum number of results (default: 10)
        search_depth: Search depth: basic or advanced (default: basic)
    """
    return await web_search.web_search_tool(query, max_results, search_depth)

@mcp.tool()
async def news_search(query: str, days: int = 7, max_results: int = 10) -> str:
    """Search for news articles with date filtering.
    Args:
        query: Search query
        days: Search within last N days (default: 7)
        max_results: Maximum number of results (default: 10)
    """
    return await news_search.news_search_tool(query, days, max_results)

if __name__ == "__main__":
    mcp.run()