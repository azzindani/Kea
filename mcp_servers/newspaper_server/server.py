
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
from mcp_servers.newspaper_server.tools import (
    article_single, source_discovery, bulk_processor, nlp_trends
)
import structlog
from typing import List, Dict, Any

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("newspaper_server", dependencies=["newspaper4k", "trafilatura", "feedparser", "httpx"])

# 1. Single Article Intelligence
# 1. Single Article Intelligence
@mcp.tool()
async def get_article_title(url: str) -> str: 
    """FETCHES article title. [ACTION]
    
    [RAG Context]
    Extract title from news article URL.
    Returns string.
    """
    return await article_single.get_article_title(url)

@mcp.tool()
async def get_article_text(url: str) -> str: 
    """FETCHES article text. [ACTION]
    
    [RAG Context]
    Extract body text from news article URL.
    Returns string.
    """
    return await article_single.get_article_text(url)

@mcp.tool()
async def get_article_authors(url: str) -> List[str]: 
    """FETCHES article authors. [ACTION]
    
    [RAG Context]
    Extract authors from news article URL.
    Returns list of strings.
    """
    return await article_single.get_article_authors(url)

@mcp.tool()
async def get_article_pubdate(url: str) -> str: 
    """FETCHES pub date. [ACTION]
    
    [RAG Context]
    Extract publication date from article URL.
    Returns date string.
    """
    return await article_single.get_article_pubdate(url)

@mcp.tool()
async def get_article_top_image(url: str) -> str: 
    """FETCHES top image. [ACTION]
    
    [RAG Context]
    Extract main image URL from article.
    Returns URL string.
    """
    return await article_single.get_article_top_image(url)

@mcp.tool()
async def get_article_nlp(url: str) -> Dict[str, Any]: 
    """ANALYZES article NLP. [ACTION]
    
    [RAG Context]
    Get summary and keywords from article.
    Returns JSON dict.
    """
    return await article_single.get_article_nlp(url)

@mcp.tool()
async def get_article_meta(url: str) -> Dict[str, Any]: 
    """FETCHES article meta. [ACTION]
    
    [RAG Context]
    Get comprehensive metadata (title, text, authors, etc).
    Returns JSON dict.
    """
    return await article_single.get_article_meta(url)

# 2. Source Intelligence
# 2. Source Intelligence
@mcp.tool()
async def build_source(url: str, memoize: bool = True) -> Dict[str, Any]: 
    """BUILDS source object. [ACTION]
    
    [RAG Context]
    Process news source domain (extract categories, feeds).
    Returns JSON dict.
    """
    return await source_discovery.build_source(url, memoize)

@mcp.tool()
async def get_source_categories(url: str) -> List[Dict[str, str]]: 
    """FETCHES source categories. [ACTION]
    
    [RAG Context]
    Get categories/topics from news source.
    Returns list of dicts.
    """
    return await source_discovery.get_source_categories(url)

@mcp.tool()
async def get_source_feeds(url: str) -> List[str]: 
    """FETCHES source feeds. [ACTION]
    
    [RAG Context]
    Get RSS/Atom feeds from news source.
    Returns list of URL strings.
    """
    return await source_discovery.get_source_feeds(url)

@mcp.tool()
async def get_source_articles_list(url: str, limit: int = 100000) -> List[str]: 
    """FETCHES article URLs. [ACTION]
    
    [RAG Context]
    Get list of article URLs from source.
    Returns list of strings.
    """
    return await source_discovery.get_source_articles_list(url, limit)

# 3. Multitalent / Bulk
@mcp.tool()
async def analyze_news_source(url: str, limit: int = 100000) -> Dict[str, Any]: 
    """ANALYZES news source. [ACTION]
    
    [RAG Context]
    Comprehensive analysis of a news source.
    Returns JSON dict.
    """
    return await bulk_processor.analyze_news_source(url, limit)

@mcp.tool()
async def bulk_article_extraction(urls: List[str], workers: int = 10) -> Dict[str, Any]: 
    """EXTRACTS bulk articles. [ACTION]
    
    [RAG Context]
    Parallel extraction of multiple articles.
    Returns JSON dict of results.
    """
    return await bulk_processor.bulk_article_extraction(urls, workers)

# 4. Trends
@mcp.tool()
async def get_google_trending_terms() -> List[str]: 
    """FETCHES Google trends. [ACTION]
    
    [RAG Context]
    Get current trending terms from Google.
    Returns list of strings.
    """
    return await nlp_trends.get_google_trending_terms()

@mcp.tool()
async def get_popular_news_sources() -> List[str]: 
    """FETCHES popular sources. [ACTION]
    
    [RAG Context]
    Get list of popular news source URLs.
    Returns list of strings.
    """
    return await nlp_trends.get_popular_news_sources()

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class NewspaperServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []
