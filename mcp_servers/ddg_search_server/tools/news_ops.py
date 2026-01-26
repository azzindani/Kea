from mcp_servers.ddg_search_server.ddg_client import DDGClient
from typing import List, Any
import asyncio

async def search_news(query: str, region: str = "wt-wt", max_results: int = 10) -> List[Any]:
    """Search news articles."""
    return await DDGClient.news(query, region=region, max_results=max_results)

async def search_news_topic(topic: str, max_results: int = 10) -> List[Any]:
    """Search news for a specific topic."""
    return await DDGClient.news(topic, max_results=max_results)

async def latest_news(query: str, max_results: int = 10) -> List[Any]:
    """Get latest news (sorted by date implied by library or default behavior)."""
    # DuckDuckGo's news endpoint usually sorts by relevance/freshness mix.
    # explicit 'timelimit=d' helps for latest.
    return await DDGClient.news(query, timelimit="d", max_results=max_results)

async def get_trending(max_results: int = 10) -> List[Any]:
    """Get trending searches via autocomplete suggestions for 'trending'."""
    # Heuristic: typing a generic char or 'trending' might give suggestions.
    # Actually DDGS doesn't have a direct 'trending' endpoint exposed clearly.
    # We'll use suggestions for a generic prompt or rely on news without query? No.
    # Let's try news for "Top Stories".
    return await DDGClient.news("Top Stories", max_results=max_results)
