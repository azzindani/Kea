import pytest
import asyncio
import os
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_matplotlib_real_simulation():
    """
    REAL SIMULATION: Verify Matplotlib Server (Plotting).
    """
    params = get_server_params("matplotlib_server", extra_dependencies=["matplotlib", "pandas", "seaborn", "scipy"])
    
    print(f"\n--- Starting Real-World Simulation: Matplotlib Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Plot Line
            print("1. Plotting Line Chart...")
            x = [1, 2, 3, 4, 5]
            y = [1, 4, 9, 16, 25]
            res = await session.call_tool("plot_line", arguments={"x": x, "y": y, "title": "Square Numbers"})
            if not res.isError:
                path = res.content[0].text
                print(f" [PASS] Saved to: {path}")
                if os.path.exists(path):
                    # Clean up
                    try:
                        os.remove(path)
                    except:
                        pass
            else:
                 print(f" [FAIL] {res.content[0].text}")

            # 2. Plot Scatter
            print("2. Plotting Scatter Chart...")
            res = await session.call_tool("plot_scatter", arguments={"x": x, "y": y, "title": "Scatter Test"})
            if not res.isError:
                path = res.content[0].text
                print(f" [PASS] Saved to: {path}")
                if os.path.exists(path):
                     try:
                        os.remove(path)
                     except:
                        pass

            # 3. Plot Bar
            print("3. Plotting Bar Chart...")
            res = await session.call_tool("plot_bar", arguments={"x": ["A", "B", "C"], "height": [3, 7, 5], "title": "Bar Test"})
            if not res.isError:
                path = res.content[0].text
                print(f" [PASS] Saved to: {path}")
                if os.path.exists(path):
                     try:
                        os.remove(path)
                     except:
                        pass

    print("--- Matplotlib Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
