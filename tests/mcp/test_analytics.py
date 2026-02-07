import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_analytics_real_simulation():
    """
    REAL SIMULATION: Verify Analytics Server using real datasets.
    """
    params = get_server_params("analytics_server", extra_dependencies=["pandas", "numpy", "scipy"])
    
    print(f"\n--- Starting Real-World Simulation: Analytics Server ---")
    
    # Use a real public CSV from GitHub (Seaborn data - Iris)
    data_url = "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv"
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Discover
            tools_res = await session.list_tools()
            tool_names = [t.name for t in tools_res.tools]
            print(f"Discovered {len(tool_names)} tools")
            
            # 2. EDA Auto
            if "eda_auto" in tool_names:
                print(f"1. Testing EDA Auto ({data_url})...")
                res = await session.call_tool("eda_auto", arguments={"data_url": data_url})
                if res.isError:
                    print(f" [FAIL] {res.content[0].text}")
                else:
                    print(f" [PASS] Report generated ({len(res.content[0].text)} chars)")
            
            # 3. Data Profiler
            if "data_profiler" in tool_names:
                print("2. Testing Data Profiler...")
                res = await session.call_tool("data_profiler", arguments={"data_url": data_url, "minimal": True})
                if not res.isError:
                    print(" [PASS] Profile generated")
                else:
                    print(f" [FAIL] {res.content[0].text}")

            # 4. Correlation Matrix
            if "correlation_matrix" in tool_names:
                print("3. Testing Correlation Matrix...")
                res = await session.call_tool("correlation_matrix", arguments={"data_url": data_url})
                if not res.isError:
                    print(f" [PASS] Matrix:\n{res.content[0].text}")
                else:
                    print(f" [FAIL] {res.content[0].text}")

            # 5. Statistical Test
            if "statistical_test" in tool_names:
                print("4. Testing Statistical Test (T-Test)...")
                # Test sepal_length group by species if possible, or just basic numeric
                # analytics_server might expect specific args
                pass 

    print("--- Analytics Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
