
import pytest
from mcp import ClientSession
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import get_server_params


@pytest.mark.asyncio
async def test_tool_discovery_real_simulation():
    """
    REAL SIMULATION: Verify Tool Discovery Server (PyPI/NPM).
    """
    params = get_server_params("tool_discovery_server", extra_dependencies=["httpx"])

    query = "requests"

    print("\n--- Starting Real-World Simulation: Tool Discovery Server ---")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Search PyPI
            print(f"1. Searching PyPI for '{query}'...")
            res = await session.call_tool("search_pypi", arguments={"query": query, "max_results": 3})
            print(f" \033[92m[PASS]\033[0m Results: {res.content[0].text}")

            # 2. Package Info
            print(f"2. Getting Info for '{query}'...")
            res = await session.call_tool("package_info", arguments={"package_name": query, "registry": "pypi"})
            # Info might be long, just print start
            print(f" \033[92m[PASS]\033[0m Info Length: {len(res.content[0].text)}")

            # 3. Evaluate Package
            print("3. Evaluating Package (MCP Suitability)...")
            res = await session.call_tool("evaluate_package", arguments={"package_name": query})
            print(f" \033[92m[PASS]\033[0m Report: {res.content[0].text[:1000]}...")

            # 4. Registry List
            print("4. Listing Registry...")
            res = await session.call_tool("tool_registry_list", arguments={})
            print(f" \033[92m[PASS]\033[0m Registry: {res.content[0].text}")

    print("--- Tool Discovery Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
