
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)


from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.scraper_server.tools import fetch_url as fetch_url_module, browser_scrape as browser_scrape_module
import structlog
from typing import Optional, Dict

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("scraper_server")

@mcp.tool()
async def fetch_url(url: str, timeout: int = 30, headers: Dict[str, str] = {}) -> str:
    """FETCHES URL. [ACTION]
    
    [RAG Context]
    Fetch URL content via HTTP GET request.
    Returns HTML content.
    """
    return await fetch_url_module.fetch_url_tool(url, timeout, headers)

@mcp.tool()
async def browser_scrape_page(url: str, wait_for: Optional[str] = None, extract_tables: bool = True, screenshot: bool = False) -> str:
    """SCRAPES page (browser). [ACTION]
    
    [RAG Context]
    Scrape URL using headless browser with JavaScript execution.
    Returns extracted content.
    """
    return await browser_scrape_module.browser_scrape_tool(url, wait_for, extract_tables, screenshot)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class ScraperServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []
