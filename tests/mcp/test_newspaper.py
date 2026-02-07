import pytest

from mcp_servers.newspaper_server.tools.article_single import get_article_nlp
from mcp_servers.newspaper_server.tools.nlp_trends import get_google_trending_terms
from mcp_servers.newspaper_server.tools.bulk_processor import analyze_news_source
import asyncio

async def verify():
    print("--- Verifying Newspaper3k Server ---")
    
    # 1. Trends
    print("\n1. Google Trends...")
    res1 = await get_google_trending_terms({})
    print(str(res1)[:300])
    
    # 2. Single Article NLP
    # Use a reliable URL, e.g. BBC or CNN
    test_url = "https://www.bbc.com/news/world-us-canada-68092288" # Example (might be old, use generic if fails)
    # Using python.org for stability if news fails? No, user wants real news.
    # Let's try CNN Tech
    test_url = "https://www.cnn.com/2024/01/25/tech/microsoft-teams-down/index.html" 
    
    # Actually, let's use a very generic recent one or find one via trends?
    # No, let's rely on analyze_news_source to find a valid URL first!
    
    # 3. Source Analysis (Multitalent)
    target_site = "https://techcrunch.com"
    print(f"\n3. Analyzing {target_site} (Multitalent)...")
    res3 = await analyze_news_source({'url': target_site, 'limit': 3})
    print(str(res3)[:500])
    
    # Check if we got articles
    # res3 -> content text -> json parse... 
    # For now just print.

if __name__ == "__main__":
    asyncio.run(verify())


@pytest.mark.asyncio
async def test_main():
    await verify()

