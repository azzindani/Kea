
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
from mcp_servers.crawler_server.tools import crawl_ops, extract_ops, inspect_ops
import structlog
from typing import Optional

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("crawler_server")

@mcp.tool()
async def web_crawler(start_url: str = None, url: str = None, max_depth: int = 1000, max_pages: int = 100000, same_domain: bool = True, delay: float = 0.5) -> str:
    """CRAWLS website recursively. [ACTION]
    
    [RAG Context]
    Args:
        max_depth: Depth limit
        same_domain: Restrict to domain
    """
    target = start_url or url
    if not target:
        return "Error: Missing 'start_url' or 'url' argument."
    return await crawl_ops.web_crawler(target, max_depth, max_pages, same_domain, delay)

@mcp.tool()
async def sitemap_parser(url: str, filter_pattern: Optional[str] = None) -> str:
    """PARSES sitemap for URLs. [DATA]
    
    [RAG Context]
    """
    return await crawl_ops.sitemap_parser(url, filter_pattern)

@mcp.tool()
async def link_extractor(url: str, filter_external: bool = False, classify: bool = False) -> str:
    """EXTRACTS links from page. [DATA]
    
    [RAG Context]
    """
    return await extract_ops.link_extractor(url, filter_external, classify)

@mcp.tool()
async def robots_checker(url: str, check_path: Optional[str] = None) -> str:
    """CHECKS robots.txt rules. [DATA]
    
    [RAG Context]
    """
    return await inspect_ops.robots_checker(url, check_path)

@mcp.tool()
async def domain_analyzer(url: str) -> str:
    """ANALYZES domain strategy. [DATA]
    
    [RAG Context]
    """
    return await inspect_ops.domain_analyzer(url)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class CrawlerServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
            return list(self.mcp._tool_manager._tools.values())
        return []
