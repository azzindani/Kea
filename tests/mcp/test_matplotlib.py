import os

import pytest
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import SafeClientSession as ClientSession
from tests.mcp.client_utils import get_server_params


@pytest.mark.asyncio
async def test_matplotlib_real_simulation():
    """
    REAL SIMULATION: Verify Matplotlib Server (Plotting).
    """
    params = get_server_params("matplotlib_server", extra_dependencies=["matplotlib", "pandas", "seaborn", "scipy"])

    print("\n--- Starting Real-World Simulation: Matplotlib Server ---")

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
                print(f" \033[92m[PASS]\033[0m Saved to: {path}")
                if os.path.exists(path):
                    # Clean up
                    try:
                        os.remove(path)
                    except:
                        pass
            else:
                 print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            # 2. Plot Scatter
            print("2. Plotting Scatter Chart...")
            res = await session.call_tool("plot_scatter", arguments={"x": x, "y": y, "title": "Scatter Test"})
            if not res.isError:
                path = res.content[0].text
                print(f" \033[92m[PASS]\033[0m Saved to: {path}")
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
                print(f" \033[92m[PASS]\033[0m Saved to: {path}")
                if os.path.exists(path):
                     try:
                        os.remove(path)
                     except:
                        pass

            # 4. Histogram
            print("4. Plotting Histogram...")
            import numpy as np
            data = np.random.randn(100).tolist()
            res = await session.call_tool("plot_hist", arguments={"x": data, "title": "Hist Test"})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Hist Saved: {res.content[0].text}")

            # 5. Heatmap
            print("5. Plotting Heatmap...")
            matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
            res = await session.call_tool("plot_heatmap", arguments={"data": matrix, "title": "Heatmap Test"})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Heatmap Saved: {res.content[0].text}")

            # 6. 3D Surface
            print("6. Plotting 3D Surface...")
            # Simple meshgrid data simulation
            X = [[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]]
            Y = [[-1, -1, -1], [0, 0, 0], [1, 1, 1]]
            Z = [[1, 0, 1], [0, 0, 0], [1, 0, 1]]
            res = await session.call_tool("plot_surface", arguments={"X": X, "Y": Y, "Z": Z, "title": "3D Test"})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m 3D Saved: {res.content[0].text}")

            # Cleanup all
            # (Assuming cleanup logic is improved or just manual check)

    print("--- Matplotlib Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
