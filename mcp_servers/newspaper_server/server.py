
from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import (
    article_single, source_discovery, bulk_processor, nlp_trends
)
import structlog
from typing import List, Dict, Any

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("newspaper_server", dependencies=["newspaper3k"])

# 1. Single Article Intelligence
@mcp.tool()
async def get_article_title(url: str) -> str: return await article_single.get_article_title(url)
@mcp.tool()
async def get_article_text(url: str) -> str: return await article_single.get_article_text(url)
@mcp.tool()
async def get_article_authors(url: str) -> List[str]: return await article_single.get_article_authors(url)
@mcp.tool()
async def get_article_pubdate(url: str) -> str: return await article_single.get_article_pubdate(url)
@mcp.tool()
async def get_article_top_image(url: str) -> str: return await article_single.get_article_top_image(url)
@mcp.tool()
async def get_article_nlp(url: str) -> Dict[str, Any]: return await article_single.get_article_nlp(url)
@mcp.tool()
async def get_article_meta(url: str) -> Dict[str, Any]: return await article_single.get_article_meta(url)

# 2. Source Intelligence
@mcp.tool()
async def build_source(url: str, memoize: bool = True) -> Dict[str, Any]: return await source_discovery.build_source(url, memoize)
@mcp.tool()
async def get_source_categories(url: str) -> List[Dict[str, str]]: return await source_discovery.get_source_categories(url)
@mcp.tool()
async def get_source_feeds(url: str) -> List[str]: return await source_discovery.get_source_feeds(url)
@mcp.tool()
async def get_source_articles_list(url: str, limit: int = 100000) -> List[str]: return await source_discovery.get_source_articles_list(url, limit)

# 3. Multitalent / Bulk
@mcp.tool()
async def analyze_news_source(url: str, limit: int = 100000) -> Dict[str, Any]: return await bulk_processor.analyze_news_source(url, limit)
@mcp.tool()
async def bulk_article_extraction(urls: List[str], workers: int = 10) -> Dict[str, Any]: return await bulk_processor.bulk_article_extraction(urls, workers)

# 4. Trends
@mcp.tool()
async def get_google_trending_terms() -> List[str]: return await nlp_trends.get_google_trending_terms()
@mcp.tool()
async def get_popular_news_sources() -> List[str]: return await nlp_trends.get_popular_news_sources()

if __name__ == "__main__":
    mcp.run()