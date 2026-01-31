from mcp_servers.google_search_server.search_client import GoogleSearchClient
from typing import List, Any, Union, Dict

async def search_google(query: str, num: int = 100, lang: str = "en", region: str = "us") -> List[Any]:
    """
    Standard Google Search.
    query: The search terms.
    num: Number of results (max ~100 per call usually).
    lang: Language code (default 'en').
    region: Region code (default 'us').
    """
    return await GoogleSearchClient.search(query, num_results=num, lang=lang, region=region)

async def search_basic(query: str, num: int = 100) -> List[str]:
    """
    Simplified search returning ONLY URLs.
    """
    results = await GoogleSearchClient.search(query, num_results=num, advanced=False)
    # Ensure list of strings
    return [str(r) for r in results]

async def search_safe(query: str, num: int = 100) -> List[Any]:
    """
    Perform a SafeSearch-enabled query.
    """
    return await GoogleSearchClient.safe_search(query, num_results=num)

async def search_images(query: str, num: int = 100) -> List[str]:
    """
    Mock Image search using 'intitle:image' or 'filetype:jpg' as google-search-python doesn't support images directly.
    A better way is to use specialized dorks.
    """
    # This library is mainly for web results. We can simulate image intent.
    # Note: Real Google Image Search API is different. This is a best-effort Web Search for images.
    dork_query = f"{query} (filetype:jpg OR filetype:png OR filetype:webp)"
    results = await GoogleSearchClient.search(dork_query, num_results=num, advanced=False)
    return [str(r) for r in results]

async def search_videos(query: str, num: int = 100) -> List[Any]:
    """
    Search specifically for video content (e.g. YouTube, Vimeo).
    """
    dork_query = f"{query} (site:youtube.com OR site:vimeo.com)"
    return await GoogleSearchClient.search(dork_query, num_results=num)
