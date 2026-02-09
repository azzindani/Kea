from mcp_servers.newspaper_server.tools.core import NewsClient
from typing import List, Dict, Any

async def build_source(url: str, memoize: bool = True) -> Dict[str, Any]:
    """Build a news source and return high-level stats."""
    try:
        s = await NewsClient.build_source(url, memoize)
        
        return {
            "url": s.get("url"),
            "brand": s.get("brand"),
            "description": s.get("description"),
            "article_count": len(s.get("article_urls", [])),
            "category_count": len(s.get("categories", [])),
            "feed_count": len(s.get("feeds", [])),
            "categories": s.get("categories", []),
            "feeds": s.get("feeds", [])
        }
    except Exception as e:
        return {"error": str(e)}

async def get_source_categories(url: str) -> List[Dict[str, str]]:
    """Get category URLs from a source."""
    try:
        s = await NewsClient.build_source(url)
        return [{"url": c, "title": "Category"} for c in s.get("categories", [])]
    except Exception as e:
        return [{"error": str(e)}]

async def get_source_feeds(url: str) -> List[str]:
    """Get RSS feed URLs from a source."""
    try:
        s = await NewsClient.build_source(url)
        return s.get("feeds", [])
    except Exception as e:
        return [str(e)]

async def get_source_articles_list(url: str, limit: int = 100000) -> List[str]:
    """Get list of article URLs found on the source (no download)."""
    try:
        s = await NewsClient.build_source(url)
        
        article_urls = s.get("article_urls", [])
        if not article_urls:
            s = await NewsClient.build_source(url, memoize=False)
            article_urls = s.get("article_urls", [])
            
        return article_urls[:limit]
    except Exception as e:
        return [str(e)]
