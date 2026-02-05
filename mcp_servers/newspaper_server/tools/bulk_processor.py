from mcp_servers.newspaper_server.tools.core import NewsClient
from newspaper import Article
import concurrent.futures
from typing import List, Dict, Any

def _process_single_article(url):
    """Helper for threading."""
    try:
        # Create fresh article object
        a = Article(url, config=NewsClient.get_config())
        a.download()
        a.parse()
        a.nlp()
        return {
            "url": url,
            "title": a.title,
            "publish_date": str(a.publish_date),
            "summary": a.summary,
            "keywords": a.keywords,
            "top_image": a.top_image,
            "status": "success"
        }
    except Exception as e:
        return {"url": url, "error": str(e), "status": "failed"}

async def bulk_article_extraction(urls: List[str], workers: int = 10) -> Dict[str, Any]:
    """
    Multithreaded download and NLP processing of a list of URLs.
    Args:
        urls: list[str]
        workers: int (default 10)
    """
    try:
        results = []
        
        # Use ThreadPoolExecutor for I/O bound tasks
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_url = {executor.submit(_process_single_article, url): url for url in urls}
            for future in concurrent.futures.as_completed(future_to_url):
                res = future.result()
                results.append(res)
                
        return {"processed": len(results), "articles": results}
        
    except Exception as e:
        return {"error": str(e)}

async def analyze_news_source(url: str, limit: int = 100000) -> Dict[str, Any]:
    """
    MULTITELENT: Scan a source, detect articles, and bulk download/analyze the top N.
    """
    try:
        # 1. Build Source
        s = NewsClient.build_source(url)
        
        # 2. Get Article URLs
        article_urls = [a.url for a in s.articles[:limit]]
        
        # 3. Bulk Process
        processed = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(_process_single_article, u): u for u in article_urls}
            for future in concurrent.futures.as_completed(futures):
                processed.append(future.result())
                
        return {
            "source": s.brand or url,
            "description": s.description,
            "discovered_count": len(s.articles),
            "analyzed_count": len(processed),
            "feed_urls": [f.url for f in s.feeds],
            "category_urls": [c.url for c in s.categories],
            "articles": processed
        }
        
    except Exception as e:
        return {"error": str(e)}
