from mcp.server.fastmcp import FastMCP
from mcp_servers.scraper_server.tools import fetch_url, browser_scrape
import structlog
from typing import Optional, Dict

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("scraper_server")

@mcp.tool()
async def fetch_url(url: str, timeout: int = 30, headers: Dict[str, str] = {}) -> str:
    """Fetch URL content via HTTP GET request.
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds (default: 30)
        headers: Optional HTTP headers
    """
    return await fetch_url.fetch_url_tool(url, timeout, headers)

@mcp.tool()
async def browser_scrape_page(url: str, wait_for: Optional[str] = None, extract_tables: bool = True, screenshot: bool = False) -> str:
    """Scrape URL using headless browser with JavaScript execution.
    Args:
        url: URL to scrape
        wait_for: CSS selector to wait for before scraping
        extract_tables: Extract tables as structured data (default: true)
        screenshot: Take screenshot (default: false)
    """
    return await browser_scrape.browser_scrape_tool(url, wait_for, extract_tables, screenshot)

if __name__ == "__main__":
    mcp.run()
