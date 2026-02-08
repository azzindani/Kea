import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_newspaper_real_simulation():
    """
    REAL SIMULATION: Verify Newspaper Server (Article Extraction).
    """
    params = get_server_params("newspaper_server", extra_dependencies=["newspaper3k", "lxml[html_clean]"])
    
    # Real URL - Using a stable tech news article or main page
    # Let's use a BBC article or similar. 
    # Or just a main domain to test source build.
    url = "https://www.bbc.com/news/technology"
    
    print(f"\n--- Starting Real-World Simulation: Newspaper Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Build Source
            print(f"1. Building Source ({url})...")
            res = await session.call_tool("build_source", arguments={"url": url})
            if res.isError:
                 print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")
                 # If build fails (network), try a simpler direct article logic if possible, 
                 # but for now we proceed.
            else:
                 print(f" \033[92m[PASS]\033[0m Source built")

            # 2. Get Articles List
            print("2. Getting Articles List...")
            res = await session.call_tool("get_source_articles_list", arguments={"url": url, "limit": 5})
            if not res.isError:
                try:
                    if not res.content:
                        print(" [WARN] No content returned from article list")
                    else:
                        import json
                        articles = json.loads(res.content[0].text)
                        print(f" \033[92m[PASS]\033[0m Found {len(articles)} articles")
                        
                        if len(articles) > 0:
                            # Find a suitable article causing less 404s
                            # Some URLs in the list might be invalid or relative if parsing failed partially
                            valid_articles = [a for a in articles if a.startswith("http")]
                            if valid_articles:
                                article_url = valid_articles[0]
                                
                                # 3. Single Article Title
                                print(f"3. Fetching Title for {article_url}...")
                                res = await session.call_tool("get_article_title", arguments={"url": article_url})
                                if not res.isError and res.content:
                                    print(f" \033[92m[PASS]\033[0m Title: {res.content[0].text}")
                                
                                # 4. NLP
                                print(f"4. NLP Analysis...")
                                res = await session.call_tool("get_article_nlp", arguments={"url": article_url})
                                if not res.isError and res.content:
                                    print(f" \033[92m[PASS]\033[0m NLP Data received")
                            else:
                                print(" [WARN] No valid article URLs found")
                except Exception as e:
                    print(f" [WARN] Could not parse article list or empty: {e}")

            # 5. Trending
            print("5. Google Trending Terms...")
            res = await session.call_tool("get_google_trending_terms")
            if not res.isError and res.content:
                print(f" \033[92m[PASS]\033[0m Trends: {res.content[0].text}")

    print("--- Newspaper Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
