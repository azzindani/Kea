import pytest
import asyncio
import os
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_plotly_real_simulation():
    """
    REAL SIMULATION: Verify Plotly Server (Visualization).
    """
    params = get_server_params("plotly_server", extra_dependencies=["plotly", "kaleido", "pandas", "numpy", "scipy"])
    
    data = [
        {"x": 1, "y": 2, "category": "A"},
        {"x": 2, "y": 3, "category": "B"},
        {"x": 3, "y": 5, "category": "A"},
        {"x": 4, "y": 8, "category": "B"}
    ]
    
    print(f"\n--- Starting Real-World Simulation: Plotly Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Scatter
            print("1. Plotting Scatter...")
            res = await session.call_tool("plot_scatter", arguments={"data": data, "x": "x", "y": "y", "color": "category"})
            if not res.isError:
                path = res.content[0].text
                print(f" [PASS] Saved to: {path}")
                if os.path.exists(path):
                    try: os.remove(path)
                    except: pass
            else:
                 print(f" [FAIL] {res.content[0].text}")

            # 2. Bar
            print("2. Plotting Bar...")
            res = await session.call_tool("plot_bar", arguments={"data": data, "x": "category", "y": "y"})
            if not res.isError:
                path = res.content[0].text
                print(f" [PASS] Saved to: {path}")
                if os.path.exists(path):
                    try: os.remove(path)
                    except: pass

            # 3. Auto Plot
            print("3. Auto Plot...")
            res = await session.call_tool("auto_plot", arguments={"data": data, "x": "x", "y": "y"})
            if not res.isError:
                 print(f" [PASS] Auto plot created")
                 path = res.content[0].text
                 if os.path.exists(path):
                    try: os.remove(path)
                    except: pass

            # 4. Candlestick
            print("4. Plotting Candlestick...")
            ohlc = [
                {"x": "2023-01-01", "open": 10, "high": 15, "low": 5, "close": 12},
                {"x": "2023-01-02", "open": 12, "high": 18, "low": 10, "close": 15}
            ]
            res = await session.call_tool("plot_candlestick", arguments={"data": ohlc, "x": "x", "open": "open", "high": "high", "low": "low", "close": "close"})
            if not res.isError:
                 print(f" [PASS] Candlestick created")
                 path = res.content[0].text
                 if os.path.exists(path):
                    try: os.remove(path)
                    except: pass

    print("--- Plotly Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
