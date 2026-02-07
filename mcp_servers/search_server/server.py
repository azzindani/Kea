
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

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
    """SEARCHES web (general). [ACTION]
    
    [RAG Context]
    Robust general purpose search using Tavily/Brave.
    Returns search results.
    """
    return await web_search.web_search_tool(query, max_results, search_depth)

@mcp.tool()
async def news_search(query: str, days: int = 7, max_results: int = 10) -> str:
    """SEARCHES news. [ACTION]
    
    [RAG Context]
    Search news articles with date filtering (lookback window).
    Returns news results.
    """
    return await news_search.news_search_tool(query, days, max_results)

if __name__ == "__main__":
    mcp.run()