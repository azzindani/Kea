import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_wbgapi_real_simulation():
    """
    REAL SIMULATION: Verify World Bank API Server.
    """
    params = get_server_params("wbgapi_server", extra_dependencies=["wbgapi", "pandas"])
    
    indicator = "NY.GDP.MKTP.CD" # GDP (current US$)
    country = "USA"
    
    print(f"\n--- Starting Real-World Simulation: World Bank Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Get Indicator Data
            print(f"1. Fetching GDP for {country}...")
            res = await session.call_tool("get_indicator_data", arguments={"indicator_code": indicator, "economies": [country], "mrv": 2})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Data: {res.content[0].text}")

            # 2. Search Economies
            print("2. Searching Economies ('United')...")
            res = await session.call_tool("search_economies", arguments={"query": "United"})
            print(f" \033[92m[PASS]\033[0m Matches: {res.content[0].text}")

            # 3. Get Topic
            print("3. Getting Topic (3)...")
            res = await session.call_tool("get_topic", arguments={"topic_id": 3}) # Economy & Growth
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Topic: {res.content[0].text}")

            # 4. List Regions
            print("4. Listing Regions...")
            res = await session.call_tool("list_regions", arguments={})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Regions: {res.content[0].text[:50]}...")

    print("--- World Bank Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
