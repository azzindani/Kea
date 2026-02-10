
import warnings
import asyncio
import httpx
import newspaper
from newspaper import Article, Source
import trafilatura
import feedparser
import nltk
from typing import Optional, List, Dict, Any
from shared.logging.structured import get_logger

logger = get_logger(__name__)

# Suppress warnings
warnings.filterwarnings("ignore", category=SyntaxWarning, module="newspaper")
import logging
logging.getLogger('newspaper.network').setLevel(logging.ERROR)
logging.getLogger('newspaper').setLevel(logging.ERROR)

# Ensure NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

class NewsClient:
    """
    Robust wrapper for news extraction using Newspaper4k and Trafilatura.
    """
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }

    @staticmethod
    def get_config() -> newspaper.Config:
        config = newspaper.Config()
        config.browser_user_agent = NewsClient.HEADERS["User-Agent"]
        config.headers = NewsClient.HEADERS
        config.request_timeout = 30
        config.number_threads = 5
        config.http_success_only = False # Allow 401/403 to be handled by higher level if needed
        return config

    @staticmethod
    async def fetch_url(url: str) -> Optional[str]:
        """Fetch URL content using httpx to bypass some blocks."""
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True, headers=NewsClient.HEADERS, http2=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    @staticmethod
    async def get_article(url: str, params: dict) -> Dict[str, Any]:
        """
        Download and parse an article with Trafilatura fallback.
        """
        html = await NewsClient.fetch_url(url)
        if not html:
            return {"error": "Failed to fetch content"}

        # Try Newspaper4k
        config = NewsClient.get_config()
        article = Article(url, config=config)
        article.set_html(html)
        article.parse()
        
        if params.get('nlp', False):
            article.nlp()

        # Try Trafilatura fallback if Newspaper4k failed to get text
        text = article.text
        if not text or len(text) < 100:
            logger.info(f"Newspaper4k extraction low quality for {url}, trying trafilatura")
            traf_text = trafilatura.extract(html, include_comments=False, include_tables=True)
            if traf_text and len(traf_text) > (len(text) if text else 0):
                text = traf_text

        return {
            "title": article.title,
            "text": text,
            "authors": article.authors,
            "publish_date": str(article.publish_date) if article.publish_date else None,
            "top_image": article.top_image,
            "summary": article.summary if hasattr(article, 'summary') else None,
            "keywords": article.keywords if hasattr(article, 'keywords') else [],
            "meta_lang": article.meta_lang,
            "meta_description": article.meta_description,
            "meta_keywords": article.meta_keywords,
            "tags": list(article.tags) if article.tags else [],
            "canonical_link": article.canonical_link,
            "html": html if params.get('include_html', False) else None
        }

    @staticmethod
    async def build_source(url: str, memoize: bool = True) -> Dict[str, Any]:
        """
        Build a news Source object using newspaper4k and feedparser.
        """
        config = NewsClient.get_config()
        config.memoize_articles = memoize
        
        # Use newspaper4k for basic discovery
        source = Source(url, config=config)
        # Since we use httpx for articles, we can't easily use source.build() 
        # because it uses its own internal fetcher. 
        # However, newspaper4k's internal fetcher is improved.
        await asyncio.to_thread(source.build)
        
        # Supplement with feedparser for better feed discovery
        feeds = [f.url for f in source.feeds]
        if not feeds:
            # Try common feed paths if newspaper failed
            feed_urls = [f"{url.rstrip('/')}/feed", f"{url.rstrip('/')}/rss", f"{url.rstrip('/')}/feeds"]
            for f_url in feed_urls:
                d = await asyncio.to_thread(feedparser.parse, f_url)
                if d.entries:
                    feeds.append(f_url)
                    break

        return {
            "url": source.url,
            "brand": source.brand,
            "description": source.description,
            "article_urls": [a.url for a in source.articles],
            "categories": [c.url for c in source.categories],
            "feeds": feeds
        }

def dict_to_result(data: Any) -> Any:
    """Helper for MCP consistency"""
    from shared.mcp.protocol import ToolResult, TextContent
    import json
    return ToolResult(
        content=[TextContent(type="text", text=json.dumps(data, indent=2, default=str))]
    )
