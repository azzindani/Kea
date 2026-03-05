
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)


from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.scraper_server.tools import fetch_url as fetch_url_module, browser_scrape as browser_scrape_module
import structlog
from typing import Optional, Dict

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

mcp = FastMCP("scraper_server")

@mcp.tool()
async def fetch_url(url: str, timeout: int = 30, headers: Dict[str, str] = {}) -> str:
    """FETCHES URL content. [ACTION]
    
    [RAG Context]
    Downloads the raw content of a specific URL using a standard HTTP GET request. This is the fastest way to retrieve static content from blogs, documentation, and news sites that do not require complex JavaScript execution.
    
    How to Use:
    - Provide the full URL including 'http://' or 'https://'.
    - Use this for simple page extractions where speed is more important than visual fidelity.
    - If the page is a "Single Page App" (React/Vue), use 'browser_scrape_page' instead.
    
    Arguments:
    - url (str): The target web address.
    - timeout (int): Seconds to wait before giving up (default 30).
    - headers (Dict): Custom HTTP headers (e.g., User-Agent).
    
    Keywords: download page, http request, curl, static extraction, web getter.
    """
    return await fetch_url_module.fetch_url_tool(url, timeout, headers)

@mcp.tool()
async def browser_scrape_page(url: str, wait_for: Optional[str] = None, extract_tables: bool = True, screenshot: bool = False) -> str:
    """SCRAPES page (browser). [ACTION]
    
    [RAG Context]
    Uses a headless browser (Playwright) to render a webpage exactly as a human would see it, including executing all JavaScript. This is essential for modern websites (React, Vue, Next.js) and pages that load content dynamically.
    
    How to Use:
    - Use this for "Heavy" sites or sites that have anti-bot protections.
    - 'wait_for': Pass a CSS selector (e.g., '.inventory-list') if the content takes time to load after the initial page load.
    - 'extract_tables': Automatically finds and converts HTML tables into clean Markdown format.
    - 'screenshot': Set to True if you need a visual verification of the page state.
    
    Arguments:
    - url (str): Target web address.
    - wait_for (str): CSS selector to wait for.
    - extract_tables (bool): Enable/disable table parsing.
    
    Keywords: headless browser, playwright, dynamic content, js rendering, stealth scraping.
    """
    return await browser_scrape_module.browser_scrape_tool(url, wait_for, extract_tables, screenshot)

from mcp_servers.scraper_server.tools import batch_scrape as batch_scrape_module

@mcp.tool()
async def batch_scrape(urls: list[str], max_concurrent: int = 5, timeout: int = 30) -> str:
    """BATCH SCRAPE multiple URLs. [ACTION]
    
    [RAG Context]
    A "Super Tool" for parallel web extraction. It fires off multiple 'fetch_url' requests simultaneously, significantly reducing the time needed to gather data from multiple sources (e.g., comparing 10 news articles).
    
    How to Use:
    - Provide a list of URLs.
    - 'max_concurrent': Controls the "politeness" and resource usage. Higher values are faster but risk being blocked.
    
    Arguments:
    - urls (List[str]): List of target web addresses.
    - max_concurrent (int): Number of parallel threads (default 5).
    
    Keywords: parallel scraping, multi-url, bulk fetch, mass extraction.
    """
    arguments = {
        "urls": urls,
        "max_concurrent": max_concurrent,
        "timeout": timeout
    }
    result = await batch_scrape_module.batch_scrape_tool(arguments)
    # Extract text content from ToolResult
    if result.content and len(result.content) > 0:
        return result.content[0].text
    return "No content returned."

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

