
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

from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.search_server.tools import web_search, news_search
import structlog

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

mcp = FastMCP("search_server")

@mcp.tool()
async def web_search(query: str, max_results: int = 10, search_depth: str = "basic") -> str:
    """SEARCHES web (general). [ACTION]
    
    [RAG Context]
    Performs a high-fidelity web search using advanced aggregators like Tavily or Brave. This is the primary entry point for gathering external real-time information, facts, and website references.
    
    How to Use:
    - Provide a natural language query (e.g., "latest advancements in solid-state batteries 2024").
    - Use 'basic' depth for fast, broad results.
    - Use 'advanced' or 'comprehensive' depth (if supported) for more detailed extraction.
    - Returns a list of snippets, titles, and source URLs.
    
    Arguments:
    - query (str): The search terms.
    - max_results (int): Number of sources to return (default 10).
    - search_depth (str): Quality level of the search.
    
    Keywords: internet search, engine, information retrieval, live facts, website finder.
    """
    try:
        return await web_search.web_search_tool(query, max_results, search_depth)
    except Exception as e:
        return f"Error executing web_search: {e}"

@mcp.tool()
async def news_search(query: str, days: int = 7, max_results: int = 10) -> str:
    """SEARCHES news. [ACTION]
    
    [RAG Context]
    Specialized search for recent news articles, press releases, and media reports. Includes a lookback window to filter for the most current events.
    
    How to Use:
    - Best for tracking current events, corporate announcements, or trending topics.
    - Set 'days' to define the freshness of the articles (e.g., 1 for today, 7 for the last week).
    
    Arguments:
    - query (str): The news topic.
    - days (int): How many days back to look for articles.
    - max_results (int): Max articles to return.
    
    Keywords: current events, breaking news, press releases, media monitoring, recent articles.
    """
    try:
        return await news_search.news_search_tool(query, days, max_results)
    except Exception as e:
        return f"Error executing news_search: {e}"

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class SearchServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []

