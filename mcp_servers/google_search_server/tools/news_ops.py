from mcp_servers.google_search_server.search_client import GoogleSearchClient
from typing import List, Any
import datetime

async def search_news(query: str, num: int = 10) -> List[Any]:
    """Generic News Search (simulated via dorks/intitle as no direct news API in basic lib)."""
    # Best effort: site:news.google.com OR intitle:news 
    # Or just generic search which usually bubbles news to top for newsy queries.
    # Note: googlesearch-python creates a Web Search.
    return await GoogleSearchClient.search(f"{query} site:news.google.com", num_results=num)

async def search_finance_news(query: str, num: int = 10) -> List[Any]:
    """Search finance news (Bloomberg, CNBC, WSJ, etc)."""
    sites = "(site:bloomberg.com OR site:cnbc.com OR site:wsj.com OR site:reuters.com OR site:finance.yahoo.com)"
    return await GoogleSearchClient.search(f"{query} {sites}", num_results=num)

async def search_tech_news(query: str, num: int = 10) -> List[Any]:
    """Search tech news (TechCrunch, Verge, HackerNews)."""
    sites = "(site:techcrunch.com OR site:theverge.com OR site:news.ycombinator.com OR site:wired.com)"
    return await GoogleSearchClient.search(f"{query} {sites}", num_results=num)

async def get_headlines_topic(topic: str, num: int = 10) -> List[Any]:
    """Get headlines for a topic from last 24h."""
    # Use "when:1d" heuristic if supported or just search text "news"
    # Assuming "after:YYYY-MM-DD" works best
    date = datetime.date.today() - datetime.timedelta(days=1)
    return await GoogleSearchClient.search(f"{topic} news after:{date.isoformat()}", num_results=num)
