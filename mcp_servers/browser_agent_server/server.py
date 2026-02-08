
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
from mcp_servers.browser_agent_server.tools import browser_ops, validation_ops, memory_ops
import structlog
from typing import List, Optional

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("browser_agent_server")

@mcp.tool()
async def human_like_search(query: str, max_sites: int = 5, min_delay: float = 1.0, max_delay: float = 3.0, focus_domains: List[str] = []) -> str:
    """SEARCHES like a human. [ACTION]
    
    [RAG Context]
    Args:
        min_delay: Minimum delay between requests
        max_delay: Maximum delay (randomized)
    """
    return await browser_ops.human_like_search(query, max_sites, min_delay, max_delay, focus_domains)

@mcp.tool()
async def source_validator(url: str, check_type: str = "basic") -> str:
    """VALIDATES source credibility. [DATA]
    
    [RAG Context]
    """
    return await validation_ops.source_validator(url, check_type)

@mcp.tool()
async def domain_scorer(domains: List[str]) -> str:
    """SCORES domain trust. [DATA]
    
    [RAG Context]
    """
    return await validation_ops.domain_scorer(domains)

@mcp.tool()
async def search_memory_add(query: str, url: str, title: str = "", summary: str = "", relevance_score: float = 0.5, credibility_score: float = 0.5) -> str:
    """STORES search result. [ACTION]
    
    [RAG Context]
    Adds to vector memory for recall.
    """
    return await memory_ops.search_memory_add(query, url, title, summary, relevance_score, credibility_score)

@mcp.tool()
async def search_memory_recall(query: str, min_relevance: float = 0.0) -> str:
    """RETRIEVES search memory. [DATA]
    
    [RAG Context]
    """
    return await memory_ops.search_memory_recall(query, min_relevance)

@mcp.tool()
async def multi_site_browse(urls: List[str], extract: str = "summary", max_concurrent: int = 10) -> str:
    """BROWSES multiple sites. [ACTION]
    
    [RAG Context]
    Parallel browsing with rate limiting.
    """
    return await browser_ops.multi_site_browse(urls, extract, max_concurrent)

if __name__ == "__main__":
    mcp.run()