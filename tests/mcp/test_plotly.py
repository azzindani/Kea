import os

import pytest
from mcp import ClientSession
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import get_server_params


@pytest.mark.asyncio
async def test_plotly_real_simulation():
    """
    REAL SIMULATION: Verify Plotly Server (Visualization).
    """
    params = get_server_params("plotly_server", extra_dependencies=["plotly", "kaleido", "pandas", "numpy", "scipy", "statsmodels"])

    data = [
        {"x": 1, "y": 2, "category": "A"},
        {"x": 2, "y": 3, "category": "B"},
        {"x": 3, "y": 5, "category": "A"},
        {"x": 4, "y": 8, "category": "B"}
    ]

    print("\n--- Starting Real-World Simulation: Plotly Server ---")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Scatter
            print("1. Plotting Scatter...")
            res = await session.call_tool("plot_scatter", arguments={"data": data, "x": "x", "y": "y", "color": "category"})
            if not res.isError:
                path = res.content[0].text
                print(f" \033[92m[PASS]\033[0m Saved to: {path}")
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass
            else:
                print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            # 2. Bar
            print("2. Plotting Bar...")
            res = await session.call_tool("plot_bar", arguments={"data": data, "x": "category", "y": "y"})
            if not res.isError:
                path = res.content[0].text
                print(f" \033[92m[PASS]\033[0m Saved to: {path}")
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass

            # 3. Auto Plot
            print("3. Auto Plot...")
            res = await session.call_tool("auto_plot", arguments={"data": data, "x": "x", "y": "y"})
            if not res.isError:
                print(" \033[92m[PASS]\033[0m Auto plot created")
                path = res.content[0].text
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass

            # 4. Candlestick
            print("4. Plotting Candlestick...")
            ohlc = [
                {"x": "2023-01-01", "open": 10, "high": 15, "low": 5, "close": 12},
                {"x": "2023-01-02", "open": 12, "high": 18, "low": 10, "close": 15}
            ]
            res = await session.call_tool("plot_candlestick", arguments={"data": ohlc, "x": "x", "open": "open", "high": "high", "low": "low", "close": "close"})
            if not res.isError:
                print(" \033[92m[PASS]\033[0m Candlestick created")
                path = res.content[0].text
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass

    print("--- Plotly Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
