import pytest

from mcp_servers.newspaper_server.tools.nlp_trends import get_google_trending_terms
from mcp_servers.newspaper_server.tools.article_single import get_article_title
import asyncio
import sys

async def verify():
    print("--- Verifying Newspaper3k Simple ---", flush=True)
    
    # 1. Trends
    print("\n1. Google Trends...", flush=True)
    try:
        res1 = await get_google_trending_terms({})
        print(str(res1)[:300], flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)
    
    # 2. Single Article
    print("\n2. Single Article...", flush=True)
    try:
        url = "https://www.python.org/"
        res2 = await get_article_title({'url': url})
        print(str(res2), flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)

if __name__ == "__main__":
    asyncio.run(verify())


@pytest.mark.asyncio
async def test_main():
    await verify()

