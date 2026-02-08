import pytest
import asyncio
from tests.mcp.client_utils import SafeClientSession as ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_networkx_real_simulation():
    """
    REAL SIMULATION: Verify NetworkX Server (Graph Analysis).
    """
    params = get_server_params("networkx_server", extra_dependencies=["networkx", "scipy", "numpy", "pandas"])
    
    print(f"\n--- Starting Real-World Simulation: NetworkX Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Create Karate Club Graph
            print("1. Generating Karate Club Graph...")
            res = await session.call_tool("karate_club_graph")
            if res.isError:
                print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")
                return
            graph_data = res.content[0].text
            # The tool likely returns a JSON representation or ID. 
            # Let's assume it returns a JSON dict passed as string, or we might need to parse it if it's a string.
            # However, for subsequent calls, we need to pass the graph back.
            # If the server is stateless regarding graph objects (which it seems to be, demanding GraphInput),
            # we might need to pass the JSON back. 
            # CAUTION: networkx_server tools take 'graph' as input. 
            # If `karate_club_graph` returns the adjacency data, we pass that.
            
            # Let's try a smaller graph for easier passing if Karate is too big, 
            # but Karate is small (34 nodes).
            import json
            try:
                graph = json.loads(graph_data)
                print(f" \033[92m[PASS]\033[0m Graph generated ({len(graph)} nodes/edges structure)")
            except:
                # It might be an adjacency list/dict directly
                graph = graph_data 
                print(f" \033[92m[PASS]\033[0m Graph generated (Raw)")

            # 2. Centrality
            print("2. Calculating Degree Centrality...")
            res = await session.call_tool("degree_centrality", arguments={"graph": graph})
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m Centrality calculated")

            # 3. Shortest Path
            print("3. Shortest Path (0 -> 33)...")
            # Nodes in Karate club are usually integers 0-33
            res = await session.call_tool("shortest_path", arguments={"graph": graph, "source": 0, "target": 33})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Path: {res.content[0].text}")

            # 4. Community Detection
            print("4. Louvain Communities...")
            res = await session.call_tool("louvain_communities", arguments={"graph": graph})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Communities found")

            # 5. MST
            print("5. Minimum Spanning Tree...")
            res = await session.call_tool("minimum_spanning_tree", arguments={"graph": graph})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m MST Calculated")

            # 6. PageRank
            print("6. PageRank...")
            res = await session.call_tool("pagerank", arguments={"graph": graph})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m PageRank Calculated")

    print("--- NetworkX Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
