from mcp.server.fastmcp import FastMCP
from mcp_servers.crawler_server.tools import crawl_ops, extract_ops, inspect_ops
import structlog
from typing import Optional

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("crawler_server")

@mcp.tool()
async def web_crawler(start_url: str, max_depth: int = 5, max_pages: int = 100, same_domain: bool = True, delay: float = 0.5) -> str:
    """Recursively crawl a website with depth control.
    Args:
        start_url: Starting URL to crawl
        max_depth: Maximum crawl depth (1-5)
        max_pages: Maximum pages to crawl (1-100)
        same_domain: Stay on same domain only
        delay: Delay between requests in seconds
    """
    return await crawl_ops.web_crawler(start_url, max_depth, max_pages, same_domain, delay)

@mcp.tool()
async def sitemap_parser(url: str, filter_pattern: Optional[str] = None) -> str:
    """Parse website sitemap for URL discovery.
    Args:
        url: Sitemap URL or website root
        filter_pattern: Regex pattern to filter URLs
    """
    return await crawl_ops.sitemap_parser(url, filter_pattern)

@mcp.tool()
async def link_extractor(url: str, filter_external: bool = False, classify: bool = False) -> str:
    """Extract all links from a webpage.
    Args:
        url: Page URL to extract links from
        filter_external: Filter out external links
        classify: Classify link types
    """
    return await extract_ops.link_extractor(url, filter_external, classify)

@mcp.tool()
async def robots_checker(url: str, check_path: Optional[str] = None) -> str:
    """Check robots.txt for allowed/disallowed paths.
    Args:
        url: Website URL
        check_path: Specific path to check
    """
    return await inspect_ops.robots_checker(url, check_path)

@mcp.tool()
async def domain_analyzer(url: str) -> str:
    """Analyze domain for crawling strategy.
    Args:
        url: Website URL to analyze
    """
    return await inspect_ops.domain_analyzer(url)

if __name__ == "__main__":
    mcp.run()
