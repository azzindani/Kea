
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.newspaper_server.tools.core import NewsClient, dict_to_result
import newspaper
from newspaper import Article
import concurrent.futures

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

async def bulk_article_extraction(arguments: dict) -> ToolResult:
    """
    Multithreaded download and NLP processing of a list of URLs.
    Args:
        urls: list[str]
        workers: int (default 10)
    """
    try:
        urls = arguments['urls']
        workers = arguments.get('workers', 10)
        
        results = []
        
        # Use ThreadPoolExecutor for I/O bound tasks
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_url = {executor.submit(_process_single_article, url): url for url in urls}
            for future in concurrent.futures.as_completed(future_to_url):
                res = future.result()
                results.append(res)
                
        return dict_to_result({"processed": len(results), "articles": results}, "Bulk Extraction Result")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def analyze_news_source(arguments: dict) -> ToolResult:
    """
    MULTITELENT: Scan a source, detect articles, and bulk download/analyze the top N.
    """
    try:
        url = arguments['url']
        limit = arguments.get('limit', 10) # How many articles to download
        
        # 1. Build Source
        s = NewsClient.build_source(url)
        
        # 2. Get Article URLs
        article_urls = [a.url for a in s.articles[:limit]]
        
        # 3. Bulk Process
        # Reuse logic? Or thread pool directly
        processed = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(_process_single_article, u): u for u in article_urls}
            for future in concurrent.futures.as_completed(futures):
                processed.append(future.result())
                
        return dict_to_result({
            "source": s.brand or url,
            "description": s.description,
            "discovered_count": len(s.articles),
            "analyzed_count": len(processed),
            "feed_urls": [f.url for f in s.feeds],
            "category_urls": [c.url for c in s.categories],
            "articles": processed
        }, f"Source Analysis: {s.brand}")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
