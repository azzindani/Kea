import pytest
import asyncio
import os
import pandas as pd
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_seaborn_real_simulation():
    """
    REAL SIMULATION: Verify Seaborn Server (Statistical Plotting).
    """
    params = get_server_params("seaborn_server", extra_dependencies=["seaborn", "matplotlib", "pandas", "numpy", "scipy"])
    
    # Create Dummy Data
    data = [
        {"x": 1, "y": 2, "group": "A"},
        {"x": 2, "y": 3, "group": "B"},
        {"x": 3, "y": 5, "group": "A"},
        {"x": 4, "y": 4, "group": "B"}
    ]
    
    print(f"\n--- Starting Real-World Simulation: Seaborn Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Scatterplot
            print("1. Scatterplot...")
            res = await session.call_tool("scatterplot", arguments={"data": data, "x": "x", "y": "y", "hue": "group"})
            if not res.isError:
                path = res.content[0].text
                print(f" [PASS] Saved to: {path}")
                if os.path.exists(path):
                    try: os.remove(path)
                    except: pass
            else:
                 print(f" [FAIL] {res.content[0].text}")

            # 2. Histplot
            print("2. Histplot...")
            res = await session.call_tool("histplot", arguments={"data": data, "x": "y"})
            if not res.isError:
                path = res.content[0].text
                print(f" [PASS] Saved to: {path}")
                if os.path.exists(path):
                    try: os.remove(path)
                    except: pass

            # 3. Complex Plots
            print("3. Complex Plots...")
            await session.call_tool("boxplot", arguments={"data": data, "x": "group", "y": "y"})
            await session.call_tool("violinplot", arguments={"data": data, "x": "group", "y": "y"})
            
            # Heatmap requires matrix data
            matrix = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
            await session.call_tool("heatmap", arguments={"data": matrix})
            
            await session.call_tool("pairplot", arguments={"data": data})

            # 4. Auto Plot
            print("3. Auto Plot...")
            res = await session.call_tool("auto_plot", arguments={"data": data, "x": "x", "y": "y"})
            if not res.isError:
                 print(f" [PASS] Auto plot created")
                 path = res.content[0].text
                 if os.path.exists(path):
                    try: os.remove(path)
                    except: pass

    print("--- Seaborn Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
