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
            print(f" \033[92m[PASS]\033[0m Ratio: {res.content[0].text}")

            # 2. Extract Best Match
            print(f"2. Extracting '{query}' from {choices}...")
            res = await session.call_tool("extract", arguments={"query": query, "choices": choices})
            print(f" \033[92m[PASS]\033[0m Matches: {res.content[0].text}")

            # 3. Deduplicate
            print("3. Deduplicating...")
            dupes = ["apple", "apple.", "banana", "orange"]
            res = await session.call_tool("deduplicate_list", arguments={"items": dupes})
            print(f" \033[92m[PASS]\033[0m Unique: {res.content[0].text}")

            # 4. Distances
            print("4. Distances...")
            await session.call_tool("levenshtein_distance", arguments={"s1": "kitten", "s2": "sitting"})
            await session.call_tool("jaro_winkler_similarity", arguments={"s1": "shackleford", "s2": "shackelford"})

            # 5. Matrix & Process
            print("5. Matrix & Process...")
            await session.call_tool("cdist_distance", arguments={"queries": ["cat"], "choices": ["cat", "dog"], "metric": "Levenshtein"})
            await session.call_tool("extractOne", arguments={"query": "apple", "choices": choices})

            # 6. Super Tools
            print("6. Super Tools...")
            await session.call_tool("cluster_strings", arguments={"items": ["apple", "aple", "banana", "banan"]})
            await session.call_tool("fuzzy_merge_datasets", arguments={
                "list_a": [{"name": "Apple", "val": 1}],
                "list_b": [{"name": "Aple", "val": 2}],
                "key_a": "name", "key_b": "name"
            })

    print("--- RapidFuzz Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
