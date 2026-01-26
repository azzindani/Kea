from mcp_servers.ddg_search_server.ddg_client import DDGClient
from typing import List, Any, Optional

async def search_text(query: str, region: str = "wt-wt", safe_search: str = "moderate", time: Optional[str] = None, max_results: int = 10) -> List[Any]:
    """
    Standard DuckDuckGo text search.
    time: d, w, m, y
    safe_search: on, moderate, off
    """
    return await DDGClient.text(query, region=region, safesearch=safe_search, timelimit=time, max_results=max_results)

async def search_private(query: str, max_results: int = 10) -> List[Any]:
    """
    Strict SafeSearch OFF search (Private/Unfiltered).
    """
    return await DDGClient.text(query, safesearch="off", max_results=max_results)

async def search_answers(query: str) -> List[Any]:
    """Get Instant Answers for a query."""
    return await DDGClient.answers(query)

async def search_suggestions(query: str, region: str = "wt-wt") -> List[Any]:
    """Get autocomplete suggestions."""
    return await DDGClient.suggestions(query, region=region)

# Time Filters
async def search_past_day(query: str, max_results: int = 10) -> List[Any]:
    return await DDGClient.text(query, timelimit="d", max_results=max_results)

async def search_past_week(query: str, max_results: int = 10) -> List[Any]:
    return await DDGClient.text(query, timelimit="w", max_results=max_results)

async def search_past_month(query: str, max_results: int = 10) -> List[Any]:
    return await DDGClient.text(query, timelimit="m", max_results=max_results)

async def search_past_year(query: str, max_results: int = 10) -> List[Any]:
    return await DDGClient.text(query, timelimit="y", max_results=max_results)

# Region Filters
async def search_region(query: str, region: str, max_results: int = 10) -> List[Any]:
    return await DDGClient.text(query, region=region, max_results=max_results)

# Specialized Wrappers
async def search_python_docs(query: str, max_results: int = 10) -> List[Any]:
    return await DDGClient.text(f"site:docs.python.org {query}", max_results=max_results)

async def search_stackoverflow(query: str, max_results: int = 10) -> List[Any]:
    return await DDGClient.text(f"site:stackoverflow.com {query}", max_results=max_results)
