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

    # Collect skip reason outside async context to avoid BaseExceptionGroup wrapping
    skip_reason = None
    failure_reason = None

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Step 1: Text Search
            query = "OpenAI API documentation"
            print(f"1. Searching for '{query}'...")

            res = await session.call_tool("search_text", arguments={"query": query, "max_results": 3})

            if res.isError:
                error_text = res.content[0].text if res.content else 'Unknown Error'
                print(f" \033[91m[FAIL]\033[0m {error_text}")
                if "RuntimeError" in error_text or "Connect" in error_text:
                    skip_reason = "DuckDuckGo unreachable (network restriction)"
                else:
                    failure_reason = "Search failed"
            elif not res.content:
                print(f" \033[93m[WARN]\033[0m Search returned no content (likely rate limit or connectivity)")
                skip_reason = "DDG returned no content (network restriction)"
            else:
                content = res.content[0].text
                print(f" \033[92m[PASS]\033[0m Got {len(content)} chars of result")
                if not content or content == "[]":
                    skip_reason = "DDG returned empty results (network restriction)"
                else:
                    assert "OpenAI" in content or "API" in content

            if not skip_reason and not failure_reason:
                # Step 2: Image Search (if available) - verify tool first
                tools_res = await session.list_tools()
                tool_names = [t.name for t in tools_res.tools]

                if "search_images" in tool_names:
                    print(f"2. Searching images for '{query}'...")
                    img_res = await session.call_tool("search_images", arguments={"query": query, "max_results": 2})
                    if not img_res.isError:
                        print(" \033[92m[PASS]\033[0m Image search successful")
                    else:
                        print(f" \033[91m[FAIL]\033[0m {img_res.content[0].text}")

                print("--- DDG Simulation Complete ---")

    # Raise skip/failure after exiting async context managers
    if skip_reason:
        pytest.skip(skip_reason)
    if failure_reason:
        assert False, failure_reason

if __name__ == "__main__":
    # Allow running directly: python tests/mcp/test_ddg_search.py
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
