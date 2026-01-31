# /// script
# dependencies = [
#   "mcp",
#   "structlog",
# ]
# ///

from mcp.server.fastmcp import FastMCP
from tools import browser_ops, validation_ops, memory_ops
import structlog
from typing import List, Optional

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("browser_agent_server")

@mcp.tool()
async def human_like_search(query: str, max_sites: int = 5, min_delay: float = 1.0, max_delay: float = 3.0, focus_domains: List[str] = []) -> str:
    """Search and browse like a human researcher with natural delays.
    Args:
        query: Search query
        max_sites: Maximum sites to visit (1-10)
        min_delay: Minimum delay between requests (seconds)
        max_delay: Maximum delay between requests (seconds)
        focus_domains: Preferred domains to prioritize
    """
    return await browser_ops.human_like_search(query, max_sites, min_delay, max_delay, focus_domains)

@mcp.tool()
async def source_validator(url: str, check_type: str = "basic") -> str:
    """Validate if a source/website is credible and legitimate.
    Args:
        url: URL to validate
        check_type: Check: basic, thorough, academic
    """
    return await validation_ops.source_validator(url, check_type)

@mcp.tool()
async def domain_scorer(domains: List[str]) -> str:
    """Score domain trustworthiness for research.
    Args:
        domains: List of domains to score
    """
    return await validation_ops.domain_scorer(domains)

@mcp.tool()
async def search_memory_add(query: str, url: str, title: str = "", summary: str = "", relevance_score: float = 0.5, credibility_score: float = 0.5) -> str:
    """Add a search result to memory for future reference.
    Args:
        query: Original search query
        url: URL of result
        title: Page title
        summary: Content summary
        relevance_score: Relevance 0-1
        credibility_score: Credibility 0-1
    """
    return await memory_ops.search_memory_add(query, url, title, summary, relevance_score, credibility_score)

@mcp.tool()
async def search_memory_recall(query: str, min_relevance: float = 0.0) -> str:
    """Recall previous search results from memory.
    Args:
        query: Query to search memory for
        min_relevance: Minimum relevance score
    """
    return await memory_ops.search_memory_recall(query, min_relevance)

@mcp.tool()
async def multi_site_browse(urls: List[str], extract: str = "summary", max_concurrent: int = 10) -> str:
    """Browse multiple sites in parallel (rate-limited).
    Args:
        urls: URLs to browse
        extract: What to extract: text, links, summary
        max_concurrent: Max parallel requests
    """
    return await browser_ops.multi_site_browse(urls, extract, max_concurrent)

if __name__ == "__main__":
    mcp.run()
