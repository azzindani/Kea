from mcp_servers.newspaper_server.tools.core import NewsClient
from typing import List, Dict, Any

async def build_source(url: str, memoize: bool = True) -> Dict[str, Any]:
    """Build a news source and return high-level stats."""
    try:
        # Heavy operation
        s = NewsClient.build_source(url, memoize)
        
        return {
            "url": s.url,
            "brand": s.brand,
            "description": s.description,
            "article_count": len(s.articles),
            "category_count": len(s.categories),
            "feed_count": len(s.feeds),
            "categories": [c.url for c in s.categories],
            "feeds": [f.url for f in s.feeds]
        }
    except Exception as e:
        return {"error": str(e)}

async def get_source_categories(url: str) -> List[Dict[str, str]]:
    """Get category URLs from a source."""
    try:
        s = NewsClient.build_source(url) # Memoized default
        return [{"url": c.url, "title": c.title} for c in s.categories]
    except Exception as e:
        return [{"error": str(e)}]

async def get_source_feeds(url: str) -> List[str]:
    """Get RSS feed URLs from a source."""
    try:
        s = NewsClient.build_source(url)
        return [f.url for f in s.feeds]
    except Exception as e:
        return [str(e)]

async def get_source_articles_list(url: str, limit: int = 100000) -> List[str]:
    """Get list of article URLs found on the source (no download)."""
    try:
        s = NewsClient.build_source(url)
        
        # If no articles found, try forcing a fresh build (bypass cache)
        # This helps if the previous build failed or was empty
        if not s.articles:
            s = NewsClient.build_source(url, memoize=False)
            
        return [a.url for a in s.articles[:limit]]
    except Exception as e:
        return [str(e)]
