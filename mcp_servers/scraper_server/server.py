
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
from tools import fetch_url as fetch_url_module, browser_scrape as browser_scrape_module
import structlog
from typing import Optional, Dict

logger = structlog.get_logger()

# Create the FastMCP server
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