
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
from mcp_servers.browser_agent_server.tools import browser_ops, validation_ops, memory_ops
import structlog
from typing import List, Optional

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

mcp = FastMCP("browser_agent_server")

@mcp.tool()
async def human_like_search(query: str, max_sites: int = 5, min_delay: float = 1.0, max_delay: float = 3.0, focus_domains: List[str] = []) -> str:
    """SEARCHES like a human. [ACTION]
    
    [RAG Context]
    A sophisticated "Super Tool" for web searching that mimics human browsing behavior to avoid anti-bot detection. It randomizes delays and interacts with search engine result pages (SERPs) realistically.
    
    How to Use:
    - 'min_delay' and 'max_delay': Range in seconds to wait between actions.
    - 'focus_domains': Restrict search results to specific trusted sites (e.g., ['wikipedia.org', 'reuters.com']).
    
    Keywords: stealth search, bot-evasion, web scraping, human mimicry.
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
    A high-throughput "Super Tool" for parallel web exploration. It fetches content from multiple URLs simultaneously using asynchronous collectors.
    
    How to Use:
    - 'extract': Choose 'summary' (AI-generated TL;DR), 'raw' (full text), or 'metadata'.
    - 'max_concurrent': Controls the number of simultaneous browser instances (default 10).
    
    Keywords: mass browsing, parallel extraction, web crawler, batch reading.
    """
    return await browser_ops.multi_site_browse(urls, extract, max_concurrent)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class BrowserAgentServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []

