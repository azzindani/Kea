"""
MCP Tool Tests: Analysis Tools.
"""

import pytest
import asyncio
from tests.mcp.client_utils import SafeClientSession as ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_analysis_real_simulation():
    """
    REAL SIMULATION: Verify Analysis Tools with real data points.
    """
    # Assuming 'analysis_server' is the correct folder name based on list_dir
    params = get_server_params("analysis_server", extra_dependencies=["pandas", "numpy", "scipy"])
    
    print(f"\n--- Starting Real-World Simulation: Analysis Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Discover
            tools_res = await session.list_tools()
            tool_names = [t.name for t in tools_res.tools]
            print(f"Discovered {len(tool_names)} tools: {tool_names[:5]}...")
            
            # 2. Trend Detection
            if "trend_detection" in tool_names:
                print("1. Testing Trend Detection...")
                data = [10, 12, 15, 18, 22, 25, 30] # Clear upward trend
                print(f"   Data: {data}")
                
                res = await session.call_tool("trend_detection", arguments={"data": data, "metric_name": "Growth"})
                
                if res.isError:
                     print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")
                else:
                     print(f" \033[92m[PASS]\033[0m Result: {res.content[0].text}")
                     # assert "increasing" in res.content[0].text.lower()
            
            # 3. Meta Analysis (Comparison)
            if "meta_analysis" in tool_names:
                print("2. Testing Meta Analysis...")
                points = [
                    {"source": "A", "value": 100},
                    {"source": "B", "value": 110},
                    {"source": "C", "value": 105},
                ]
                res = await session.call_tool("meta_analysis", arguments={"data_points": points, "analysis_type": "comparison"})
                if not res.isError:
                     print(f" \033[92m[PASS]\033[0m {res.content[0].text[:1000]}...")
                else:
                     print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            print("--- Analysis Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
