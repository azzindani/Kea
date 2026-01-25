
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.newspaper_server.tools.core import NewsClient, dict_to_result
import json

async def get_article_title(arguments: dict) -> ToolResult:
    """Get the title of an article."""
    try:
        url = arguments['url']
        a = NewsClient.get_article(url, {})
        return dict_to_result({"title": a.title}, "Article Title")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_article_text(arguments: dict) -> ToolResult:
    """Get the main body text of an article."""
    try:
        url = arguments['url']
        a = NewsClient.get_article(url, {})
        return dict_to_result({"text": a.text}, "Article Text")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_article_authors(arguments: dict) -> ToolResult:
    """Get authors of an article."""
    try:
        url = arguments['url']
        a = NewsClient.get_article(url, {})
        return dict_to_result({"authors": a.authors}, "Article Authors")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_article_pubdate(arguments: dict) -> ToolResult:
    """Get publication date."""
    try:
        url = arguments['url']
        a = NewsClient.get_article(url, {})
        return dict_to_result({"publish_date": a.publish_date}, "Article PubDate")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_article_top_image(arguments: dict) -> ToolResult:
    """Get the main image URL."""
    try:
        url = arguments['url']
        a = NewsClient.get_article(url, {})
        return dict_to_result({"top_image": a.top_image}, "Article Top Image")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_article_nlp(arguments: dict) -> ToolResult:
    """Get NLP analysis (Summary & Keywords)."""
    try:
        url = arguments['url']
        a = NewsClient.get_article(url, {'nlp': True})
        return dict_to_result({
            "summary": a.summary,
            "keywords": a.keywords
        }, "Article NLP")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_article_meta(arguments: dict) -> ToolResult:
    """Get robust metadata (lang, description, tags)."""
    try:
        url = arguments['url']
        a = NewsClient.get_article(url, {})
        return dict_to_result({
            "meta_lang": a.meta_lang,
            "meta_description": a.meta_description,
            "meta_keywords": a.meta_keywords,
            "tags": list(a.tags),
            "canonical_link": a.canonical_link
        }, "Article Metadata")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
