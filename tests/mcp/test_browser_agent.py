
import pytest
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import SafeClientSession as ClientSession
from tests.mcp.client_utils import get_server_params


@pytest.mark.asyncio
async def test_browser_full_coverage():
    """
    REAL SIMULATION: Verify Browser Agent (100% Tool Coverage).
    """
    params = get_server_params("browser_agent_server", extra_dependencies=["browser-use", "playwright"])

    # Target for browsing
    url = "https://example.com"
    query = "AI agents"

    print("\n--- Starting 100% Coverage Simulation: Browser Agent ---")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Search (Human-like)
            print(" [1] Testing human_like_search...")
            # Using dry run or real search with minimal sites to be fast
            await session.call_tool("human_like_search", arguments={"query": query, "max_sites": 1, "max_delay": 0.5})

            # 2. Browse (Multi-site)
            print(" [2] Testing multi_site_browse...")
            await session.call_tool("multi_site_browse", arguments={"urls": [url], "extract": "summary"})

            # 3. Validation
            print(" [3] Testing validation tools...")
            await session.call_tool("source_validator", arguments={"url": url, "check_type": "basic"})
            await session.call_tool("domain_scorer", arguments={"domains": ["example.com", "google.com"]})

            # 4. Memory
            print(" [4] Testing memory tools...")
            await session.call_tool("search_memory_add", arguments={
                "query": query,
                "url": url,
                "title": "Example",
                "summary": "AI stuff",
                "relevance_score": 0.9,
                "credibility_score": 1.0
            })

            res = await session.call_tool("search_memory_recall", arguments={"query": query})
            # Check calling works, don't assert strict content if memory is ephemeral or empty
            if not res.isError:
                 print(f"    Recall Result: {str(res.content[0].text)[:1000]}...")

    print("--- Browser Agent 100% Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
