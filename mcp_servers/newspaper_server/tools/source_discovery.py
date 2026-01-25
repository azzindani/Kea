
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.newspaper_server.tools.core import NewsClient, dict_to_result
import newspaper

async def build_source(arguments: dict) -> ToolResult:
    """Build a news source and return high-level stats."""
    try:
        url = arguments['url']
        memoize = arguments.get('memoize', True)
        
        # Heavy operation
        s = NewsClient.build_source(url, memoize)
        
        return dict_to_result({
            "url": s.url,
            "brand": s.brand,
            "description": s.description,
            "article_count": len(s.articles),
            "category_count": len(s.categories),
            "feed_count": len(s.feeds),
            "categories": [c.url for c in s.categories],
            "feeds": [f.url for f in s.feeds]
        }, f"Source Build: {s.brand}")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_source_categories(arguments: dict) -> ToolResult:
    """Get category URLs from a source."""
    try:
        url = arguments['url']
        s = NewsClient.build_source(url) # Memoized default
        cats = [{"url": c.url, "title": c.title} for c in s.categories]
        return dict_to_result(cats, "Source Categories")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_source_feeds(arguments: dict) -> ToolResult:
    """Get RSS feed URLs from a source."""
    try:
        url = arguments['url']
        s = NewsClient.build_source(url)
        feeds = [f.url for f in s.feeds]
        return dict_to_result(feeds, "Source Feeds")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_source_articles_list(arguments: dict) -> ToolResult:
    """Get list of article URLs found on the source (no download)."""
    try:
        url = arguments['url']
        limit = arguments.get('limit', 50)
        s = NewsClient.build_source(url)
        
        articles = [a.url for a in s.articles[:limit]]
        return dict_to_result(articles, f"Source Articles (Top {limit})")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
