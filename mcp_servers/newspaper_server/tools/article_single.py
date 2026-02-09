from mcp_servers.newspaper_server.tools.core import NewsClient
from typing import Dict, List, Any

async def get_article_title(url: str) -> str:
    """Get the title of an article."""
    try:
        a = await NewsClient.get_article(url, {})
        return a.get("title", "Unknown Title")
    except Exception as e:
        return f"Error: {str(e)}"

async def get_article_text(url: str) -> str:
    """Get the main body text of an article."""
    try:
        a = await NewsClient.get_article(url, {})
        return a.get("text", "No text found")
    except Exception as e:
        return f"Error: {str(e)}"

async def get_article_authors(url: str) -> List[str]:
    """Get authors of an article."""
    try:
        a = await NewsClient.get_article(url, {})
        return a.get("authors", [])
    except Exception as e:
        return []

async def get_article_pubdate(url: str) -> str:
    """Get publication date."""
    try:
        a = await NewsClient.get_article(url, {})
        return a.get("publish_date", "None")
    except Exception as e:
        return f"Error: {str(e)}"

async def get_article_top_image(url: str) -> str:
    """Get the main image URL."""
    try:
        a = await NewsClient.get_article(url, {})
        return a.get("top_image", "")
    except Exception as e:
        return f"Error: {str(e)}"

async def get_article_nlp(url: str) -> Dict[str, Any]:
    """Get NLP analysis (Summary & Keywords)."""
    try:
        a = await NewsClient.get_article(url, {'nlp': True})
        return {
            "summary": a.get("summary"),
            "keywords": a.get("keywords", [])
        }
    except Exception as e:
        return {"error": str(e)}

async def get_article_meta(url: str) -> Dict[str, Any]:
    """Get robust metadata (lang, description, tags)."""
    try:
        a = await NewsClient.get_article(url, {})
        return {
            "meta_lang": a.get("meta_lang"),
            "meta_description": a.get("meta_description"),
            "meta_keywords": a.get("meta_keywords"),
            "tags": a.get("tags", []),
            "canonical_link": a.get("canonical_link")
        }
    except Exception as e:
        return {"error": str(e)}
