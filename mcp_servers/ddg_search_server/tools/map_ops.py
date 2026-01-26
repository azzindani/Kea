from mcp_servers.ddg_search_server.ddg_client import DDGClient
from typing import List, Any

async def search_places(query: str, max_results: int = 10) -> List[Any]:
    """Search for places/businesses."""
    return await DDGClient.maps(query, max_results=max_results)

async def get_address(query: str) -> List[Any]:
    """
    Search for address details.
    Uses maps endpoint but focuses on finding specific address info.
    """
    return await DDGClient.maps(query, max_results=1)

async def find_near_me(query: str, max_results: int = 10) -> List[Any]:
    """
    Search for places near 'me' (uses IP geo or just text query 'near me').
    DDG handles 'near me' in query well.
    """
    return await DDGClient.maps(f"{query} near me", max_results=max_results)
