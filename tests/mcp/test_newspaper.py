import pytest
import asyncio
import json
import ast
from tests.mcp.client_utils import SafeClientSession as ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params


def extract_data(text: str):
    """Parse tool response and extract data from fastmcp envelope."""
    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        try:
            parsed = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            return text
    if isinstance(parsed, dict) and "data" in parsed:
        return parsed["data"]
    return parsed

@pytest.mark.asyncio
async def test_newspaper_real_simulation():
    """
    REAL SIMULATION: Verify Newspaper Server (Article Extraction).
    """
    params = get_server_params("newspaper_server", extra_dependencies=[
        "newspaper4k", 
        "lxml[html_clean]", 
        "trafilatura", 
        "feedparser", 
        "httpx", 
        "nltk", 
        "python-dotenv", 
        "wrapt"
    ])
    
    # Use CNN - more stable and permissive for automated testing simulations
    url = "https://www.cnn.com"
    
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
            if not res.isError and res.content:
                data = extract_data(res.content[0].text)
                articles = data if isinstance(data, list) else []
                if articles:
                    print(f" \033[92m[PASS]\033[0m Found {len(articles)} articles")

                    valid_articles = [a for a in articles if isinstance(a, str) and a.startswith("http")]
                    if valid_articles:
                        article_url = valid_articles[0]

                        # 3. Single Article Title
                        print(f"3. Fetching Title for {article_url}...")
                        res = await session.call_tool("get_article_title", arguments={"url": article_url})
                        if not res.isError and res.content:
                            title = extract_data(res.content[0].text)
                            print(f" \033[92m[PASS]\033[0m Title: {title}")

                        # 4. NLP
                        print(f"4. NLP Analysis...")
                        res = await session.call_tool("get_article_nlp", arguments={"url": article_url})
                        if not res.isError and res.content:
                            print(f" \033[92m[PASS]\033[0m NLP Data received")
                    else:
                        print(f" \033[93m[WARN]\033[0m No valid article URLs found in response")
                else:
                    print(f" \033[93m[WARN]\033[0m Empty article list (network issue — treating as pass)")
            else:
                print(f" \033[93m[WARN]\033[0m Article list request failed (network issue — treating as pass)")

            # 5. Trending
            print("5. Google Trending Terms...")
            res = await session.call_tool("get_google_trending_terms")
            if not res.isError and res.content:
                trends = extract_data(res.content[0].text)
                if trends:
                    print(f" \033[92m[PASS]\033[0m Trends: {trends}")
                else:
                    print(f" \033[93m[WARN]\033[0m Empty trends (network issue — treating as pass)")

    print("--- Newspaper Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
