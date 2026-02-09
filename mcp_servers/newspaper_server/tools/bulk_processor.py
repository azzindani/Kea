import asyncio
from mcp_servers.newspaper_server.tools.core import NewsClient
from typing import List, Dict, Any

async def _process_single_article(url):
    """Helper for async processing."""
    try:
        a = await NewsClient.get_article(url, {'nlp': True})
        if "error" in a:
            return {"url": url, "error": a["error"], "status": "failed"}
            
        return {
            "url": url,
            "title": a.get("title"),
            "publish_date": a.get("publish_date"),
            "summary": a.get("summary"),
            "keywords": a.get("keywords"),
            "top_image": a.get("top_image"),
            "status": "success"
        }
    except Exception as e:
        return {"url": url, "error": str(e), "status": "failed"}

async def bulk_article_extraction(urls: List[str], workers: int = 10) -> Dict[str, Any]:
    """
    Asynchronous download and NLP processing of a list of URLs.
    Args:
        urls: list[str]
        workers: int (not used with asyncio, but kept for signature compatibility)
    """
    try:
        tasks = [_process_single_article(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return {"processed": len(results), "articles": results}
    except Exception as e:
        return {"error": str(e)}

async def analyze_news_source(url: str, limit: int = 100000) -> Dict[str, Any]:
    """
    MULTITELENT: Scan a source, detect articles, and bulk download/analyze the top N.
    """
    try:
        # 1. Build Source
        s = await NewsClient.build_source(url)
        
        # 2. Get Article URLs
        article_urls = s.get("article_urls", [])[:limit]
        
        # 3. Bulk Process
        if article_urls:
            tasks = [_process_single_article(u) for u in article_urls]
            processed = await asyncio.gather(*tasks)
        else:
            processed = []
                
        return {
            "source": s.get("brand") or url,
            "description": s.get("description"),
            "discovered_count": len(s.get("article_urls", [])),
            "analyzed_count": len(processed),
            "feed_urls": s.get("feeds", []),
            "category_urls": s.get("categories", []),
            "articles": processed
        }
        
    except Exception as e:
        return {"error": str(e)}
