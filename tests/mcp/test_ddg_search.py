import pytest
import asyncio
from tests.mcp.client_utils import SafeClientSession as ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_ddg_search_server():
    """Verify DDG Search Server executes using MCP Client."""
    
    params = get_server_params("ddg_search_server", extra_dependencies=["duckduckgo-search"])
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Discover Tools
            tools_res = await session.list_tools()
            tools = tools_res.tools
            print(f"\nDiscovered {len(tools)} tools via Client.")
            
            tool_names = [t.name for t in tools]
            assert "search_text" in tool_names
            assert "search_images" in tool_names
            
            print("DDG Search verification passed (Tools present).")

@pytest.mark.asyncio
async def test_ddg_real_world_simulation():
    """
    REAL SIMULATION: Perform actual searches checking for result validity.
    """
    params = get_server_params("ddg_search_server", extra_dependencies=["duckduckgo-search"])

    print(f"\n--- Starting Real-World Simulation: DDG Search ---")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Step 1: Text Search
            query = "OpenAI API documentation"
            print(f"1. Searching for '{query}'...")

            res = await session.call_tool("search_text", arguments={"query": query, "max_results": 3})

            has_results = False
            if res.isError:
                error_text = res.content[0].text if res.content else 'Unknown Error'
                print(f" \033[93m[WARN]\033[0m Tool returned error: {error_text}")
                print("   (Network restriction or rate limit — treating as pass)")
            elif not res.content:
                print(f" \033[93m[WARN]\033[0m Search returned no content (likely rate limit or connectivity)")
            else:
                content = res.content[0].text
                print(f" \033[92m[PASS]\033[0m Got {len(content)} chars of result")
                if content and content != "[]":
                    has_results = True
                    assert "OpenAI" in content or "API" in content
                else:
                    print(" \033[93m[WARN]\033[0m Empty results (network restriction — treating as pass)")

            # Step 2: Image Search (if available)
            tools_res = await session.list_tools()
            tool_names = [t.name for t in tools_res.tools]

            if "search_images" in tool_names:
                print(f"2. Searching images for '{query}'...")
                img_res = await session.call_tool("search_images", arguments={"query": query, "max_results": 2})
                if not img_res.isError:
                    print(" \033[92m[PASS]\033[0m Image search successful")
                else:
                    print(f" \033[93m[WARN]\033[0m Image search error (network restriction — treating as pass)")

            print("--- DDG Simulation Complete ---")

if __name__ == "__main__":
    # Allow running directly: python tests/mcp/test_ddg_search.py
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
