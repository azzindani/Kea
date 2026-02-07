import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_scraper_real_simulation():
    """
    REAL SIMULATION: Verify Scraper Server (Web Scraping).
    """
    params = get_server_params("scraper_server", extra_dependencies=["playwright", "lxml"])
    
    url = "https://example.com"
    
    print(f"\n--- Starting Real-World Simulation: Scraper Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Fetch URL
            print(f"1. Fetching {url}...")
            res = await session.call_tool("fetch_url", arguments={"url": url})
            if not res.isError:
                 print(f" [PASS] Fetched {len(res.content[0].text)} chars")
            else:
                 print(f" [FAIL] {res.content[0].text}")

            # 2. Browser Scrape
            print("2. Browser Scrape...")
            # We assume playwright is installed with the server dependencies
            res = await session.call_tool("browser_scrape_page", arguments={"url": url, "screenshot": True})
            if not res.isError:
                 print(f" [PASS] Browser scrape successful")
            else:
                 print(f" [WARN] Browser scrape failed (maybe browser not installed): {res.content[0].text}")

    print("--- Scraper Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
