
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.newspaper_server.tools.core import NewsClient, dict_to_result
import newspaper

async def get_google_trending_terms(arguments: dict) -> ToolResult:
    """Get Google trending search terms."""
    try:
        hot = newspaper.hot()
        return dict_to_result(hot, "Google Trending Terms")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_popular_news_sources(arguments: dict) -> ToolResult:
    """Get list of popular news source URLs."""
    try:
        pop = newspaper.popular_urls()
        return dict_to_result(pop, "Popular News Sources")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
