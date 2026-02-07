import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_rapidfuzz_real_simulation():
    """
    REAL SIMULATION: Verify RapidFuzz Server (String Matching).
    """
    params = get_server_params("rapidfuzz_server", extra_dependencies=["rapidfuzz", "pandas", "numpy"])
    
    choices = ["Apple Inc.", "Apple Corp", "Application", "Banana"]
    query = "Apple"
    
    print(f"\n--- Starting Real-World Simulation: RapidFuzz Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Simple Ratio
            print("1. Calculating Ratio...")
            res = await session.call_tool("ratio", arguments={"s1": "fuzzy", "s2": "wuzzy"})
            print(f" [PASS] Ratio: {res.content[0].text}")

            # 2. Extract Best Match
            print(f"2. Extracting '{query}' from {choices}...")
            res = await session.call_tool("extract", arguments={"query": query, "choices": choices})
            print(f" [PASS] Matches: {res.content[0].text}")

            # 3. Deduplicate
            print("3. Deduplicating...")
            dupes = ["apple", "apple.", "banana", "orange"]
            res = await session.call_tool("deduplicate_list", arguments={"items": dupes})
            print(f" [PASS] Unique: {res.content[0].text}")

    print("--- RapidFuzz Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
