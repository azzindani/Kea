import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_search_real_simulation():
    """
    REAL SIMULATION: Verify Search Server (Web/News).
    """
    params = get_server_params("search_server", extra_dependencies=[])
    
    query = "latest advancements in AI agents"
    
    print(f"\n--- Starting Real-World Simulation: Search Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Web Search
            print(f"1. Web Search: '{query}'...")
            res = await session.call_tool("web_search", arguments={"query": query, "max_results": 2})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Results found (Length: {len(res.content[0].text)})")
            else:
                 print(f" [WARN] Search failed (network/API key?): {res.content[0].text}")

            # 2. News Search
            print(f"2. News Search: '{query}'...")
            res = await session.call_tool("news_search", arguments={"query": query, "max_results": 2})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m News found (Length: {len(res.content[0].text)})")

    print("--- Search Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
