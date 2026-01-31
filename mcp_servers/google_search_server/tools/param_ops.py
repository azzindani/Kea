from mcp_servers.google_search_server.search_client import GoogleSearchClient
from typing import List, Any

# Time Filters (Note: googlesearch-python doesn't natively support 'tbs' parameter perfectly in all forks, 
# but we can try appending dorks or using 'when' parameter if available. 
# The standard `search` function supports `tbs` (time based search) in some versions.
# If not, we can simulate with "after:YYYY-MM-DD" dorks, but relative times (past hour) need parameters.
# We will use "after:YYYY-MM-DD" dorks relative to NOW for simplicity and robustness.)

import datetime

def _get_date_dork(days_ago: int) -> str:
    date = datetime.date.today() - datetime.timedelta(days=days_ago)
    return f"after:{date.isoformat()}"

async def search_past_hour(query: str, num: int = 100) -> List[Any]:
    """
    Search results from the past hour. 
    (Note: Hard to dork 'hour', usually needs 'tbs=qdr:h'. 
    If library ignores it, we fallback to just search. 
    Here we assume standard search, but append text 'last hour' as soft filter or use library features limitation).
    """
    # Best effort without native 'tbs' support in simple wrapper:
    return await GoogleSearchClient.search(query + " after:2024 (simulating fresh)", num_results=num)

async def search_past_day(query: str, num: int = 100) -> List[Any]:
    """Search results from the past 24 hours."""
    dork = _get_date_dork(1)
    return await GoogleSearchClient.search(f"{query} {dork}", num_results=num)

async def search_past_week(query: str, num: int = 100) -> List[Any]:
    """Search results from the past week."""
    dork = _get_date_dork(7)
    return await GoogleSearchClient.search(f"{query} {dork}", num_results=num)

async def search_past_month(query: str, num: int = 100) -> List[Any]:
    """Search results from the past month."""
    dork = _get_date_dork(30)
    return await GoogleSearchClient.search(f"{query} {dork}", num_results=num)

async def search_past_year(query: str, num: int = 100) -> List[Any]:
    """Search results from the past year."""
    dork = _get_date_dork(365)
    return await GoogleSearchClient.search(f"{query} {dork}", num_results=num)

async def search_region(query: str, region: str, num: int = 100) -> List[Any]:
    """Search within a specific region (gl parameter)."""
    return await GoogleSearchClient.search(query, region=region, num_results=num)

async def search_us(query: str, num: int = 100) -> List[Any]:
    """Search USA region."""
    return await GoogleSearchClient.search(query, region="us", num_results=num)

async def search_uk(query: str, num: int = 100) -> List[Any]:
    """Search UK region."""
    return await GoogleSearchClient.search(query, region="uk", num_results=num)

async def search_language(query: str, lang: str, num: int = 100) -> List[Any]:
    """Search in specific language (lr parameter)."""
    return await GoogleSearchClient.search(query, lang=lang, num_results=num)
