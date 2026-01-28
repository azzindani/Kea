from mcp_servers.newspaper_server.tools.core import NewsClient
from typing import Dict, List, Any

async def get_article_title(url: str) -> str:
    """Get the title of an article."""
    try:
        a = NewsClient.get_article(url, {})
        return a.title
    except Exception as e:
        return f"Error: {str(e)}"

async def get_article_text(url: str) -> str:
    """Get the main body text of an article."""
    try:
        a = NewsClient.get_article(url, {})
        return a.text
    except Exception as e:
        return f"Error: {str(e)}"

async def get_article_authors(url: str) -> List[str]:
    """Get authors of an article."""
    try:
        a = NewsClient.get_article(url, {})
        return a.authors
    except Exception as e:
        return []

async def get_article_pubdate(url: str) -> str:
    """Get publication date."""
    try:
        a = NewsClient.get_article(url, {})
        return str(a.publish_date)
    except Exception as e:
        return f"Error: {str(e)}"

async def get_article_top_image(url: str) -> str:
    """Get the main image URL."""
    try:
        a = NewsClient.get_article(url, {})
        return a.top_image
    except Exception as e:
        return f"Error: {str(e)}"

async def get_article_nlp(url: str) -> Dict[str, Any]:
    """Get NLP analysis (Summary & Keywords)."""
    try:
        a = NewsClient.get_article(url, {'nlp': True})
        return {
            "summary": a.summary,
            "keywords": a.keywords
        }
    except Exception as e:
        return {"error": str(e)}

async def get_article_meta(url: str) -> Dict[str, Any]:
    """Get robust metadata (lang, description, tags)."""
    try:
        a = NewsClient.get_article(url, {})
        return {
            "meta_lang": a.meta_lang,
            "meta_description": a.meta_description,
            "meta_keywords": a.meta_keywords,
            "tags": list(a.tags),
            "canonical_link": a.canonical_link
        }
    except Exception as e:
        return {"error": str(e)}
