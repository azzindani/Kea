from mcp_servers.ddg_search_server.ddg_client import DDGClient
from typing import List, Any, Dict
import asyncio

async def bulk_text_search(queries: List[str], max_results: int = 5) -> Dict[str, List[Any]]:
    """Execute multiple text searches."""
    results = {}
    for q in queries:
        # DDGS usually handles rate limits well, but safe to sleep slightly
        res = await DDGClient.text(q, max_results=max_results)
        results[q] = res
        await asyncio.sleep(1.0)
    return results

async def bulk_image_search(queries: List[str], max_results: int = 5) -> Dict[str, List[Any]]:
    """Execute multiple image searches."""
    results = {}
    for q in queries:
        res = await DDGClient.images(q, max_results=max_results)
        results[q] = res
        await asyncio.sleep(1.0)
    return results

async def bulk_news_search(queries: List[str], max_results: int = 5) -> Dict[str, List[Any]]:
    """Execute multiple news searches."""
    results = {}
    for q in queries:
        res = await DDGClient.news(q, max_results=max_results)
        results[q] = res
        await asyncio.sleep(1.0)
    return results
