from mcp_servers.newspaper_server.tools.core import NewsClient
import newspaper
from typing import List

async def get_google_trending_terms() -> List[str]:
    """Get Google trending search terms."""
    try:
        return newspaper.hot()
    except Exception as e:
        return [str(e)]

async def get_popular_news_sources() -> List[str]:
    """Get list of popular news source URLs."""
    try:
        return newspaper.popular_urls()
    except Exception as e:
        return [str(e)]
