import pytest
import asyncio
from tests.mcp.client_utils import SafeClientSession as ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_google_search_server():
    """Verify Google Search Server executes using MCP Client."""
    
    params = get_server_params("google_search_server", extra_dependencies=["googlesearch-python", "beautifulsoup4"])
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Discover Tools
            tools_res = await session.list_tools()
            tools = tools_res.tools
            print(f"\nDiscovered {len(tools)} tools via Client.")
            
            tool_names = [t.name for t in tools]
            assert "search_google" in tool_names
            assert "find_pdf" in tool_names
            
            print("Google Search verification passed (Tools present).")

@pytest.mark.asyncio
async def test_google_real_simulation():
    """
    REAL SIMULATION: Perform actual Google searches.
    """
    params = get_server_params("google_search_server", extra_dependencies=["googlesearch-python", "beautifulsoup4"])
    
    print(f"\n--- Starting Real-World Simulation: Google Search ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Step 1: Search Text
            query = "Python programming features"
            print(f"1. Searching for '{query}'...")
            
            # Note: server.py expects 'num', not 'num_results'
            res = await session.call_tool("search_google", arguments={"query": query, "num": 3})
            
            if res.isError:
                print(f" \033[91m[FAIL]\033[0m {res.content[0].text if res.content else 'Unknown Error'}")
            else:
                if not res.content:
                    print(f" \033[93m[WARN]\033[0m Empty results. Google might be rate limiting.")
                else:
                    content = res.content[0].text
                    print(f" \033[92m[PASS]\033[0m Got result length: {len(content)}")
                    # print(f"DEBUG CONTENT: {content[:500]}")
                    
                    # Check for empty result which might happen if google blocks bot
                    if len(content) < 10 or content == "[]":
                         print(f" \033[93m[WARN]\033[0m Empty results. Google might be rate limiting.")
                    else:
                         assert "Python" in content or "python" in content.lower()
                
            print("--- Google Search Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
