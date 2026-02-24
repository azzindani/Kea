from typing import Any

import pytest
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import SafeClientSession as ClientSession
from tests.mcp.client_utils import get_server_params


@pytest.mark.asyncio
async def test_networkx_real_simulation():
    """
    REAL SIMULATION: Verify NetworkX Server (Graph Analysis).
    """
    params = get_server_params("networkx_server", extra_dependencies=["networkx", "scipy", "numpy", "pandas"])

    print("\n--- Starting Real-World Simulation: NetworkX Server ---")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Helper to extract data from fastmcp response envelope
            def extract_data(text: str) -> Any:
                """Parse tool response and extract data from fastmcp envelope."""
                import ast
                import json
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

            # 1. Create Karate Club Graph
            print("1. Generating Karate Club Graph...")
            res = await session.call_tool("karate_club_graph")
            assert not res.isError, f"karate_club_graph failed: {res.content[0].text if res.content else 'Unknown'}"
            graph = extract_data(res.content[0].text)
            assert isinstance(graph, dict), f"Expected dict graph, got {type(graph)}"
            print(f" \033[92m[PASS]\033[0m Graph generated ({len(graph.get('nodes', []))} nodes)")

            # 2. Centrality
            print("2. Calculating Degree Centrality...")
            res = await session.call_tool("degree_centrality", arguments={"graph": graph})
            assert not res.isError, f"degree_centrality failed: {res.content[0].text if res.content else 'Unknown'}"
            print(" \033[92m[PASS]\033[0m Centrality calculated")

            # 3. Shortest Path
            print("3. Shortest Path (0 -> 33)...")
            res = await session.call_tool("shortest_path", arguments={"graph": graph, "source": 0, "target": 33})
            assert not res.isError, f"shortest_path failed: {res.content[0].text if res.content else 'Unknown'}"
            print(" \033[92m[PASS]\033[0m Path found")

            # 4. Community Detection
            print("4. Louvain Communities...")
            res = await session.call_tool("louvain_communities", arguments={"graph": graph})
            assert not res.isError, f"louvain_communities failed: {res.content[0].text if res.content else 'Unknown'}"
            print(" \033[92m[PASS]\033[0m Communities found")

            # 5. MST
            print("5. Minimum Spanning Tree...")
            res = await session.call_tool("minimum_spanning_tree", arguments={"graph": graph})
            assert not res.isError, f"minimum_spanning_tree failed: {res.content[0].text if res.content else 'Unknown'}"
            print(" \033[92m[PASS]\033[0m MST Calculated")

            # 6. PageRank
            print("6. PageRank...")
            res = await session.call_tool("pagerank", arguments={"graph": graph})
            assert not res.isError, f"pagerank failed: {res.content[0].text if res.content else 'Unknown'}"
            print(" \033[92m[PASS]\033[0m PageRank Calculated")

    print("--- NetworkX Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
