import os

import numpy as np
import pandas as pd
import pytest
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import SafeClientSession as ClientSession
from tests.mcp.client_utils import get_server_params


@pytest.mark.asyncio
async def test_portfolio_real_simulation():
    """
    REAL SIMULATION: Verify Portfolio Server (Optimization).
    """
    params = get_server_params("portfolio_server", extra_dependencies=["pyportfolioopt", "pandas", "numpy", "matplotlib", "scipy"])

    # Create Dummy Prices CSV
    csv_file = "test_prices.csv"
    dates = pd.date_range(start="2023-01-01", periods=100)
    data = np.random.randn(100, 3).cumsum(axis=0) + 100
    df = pd.DataFrame(data, index=dates, columns=["AAPL", "GOOG", "MSFT"])
    df.to_csv(csv_file)

    print("\n--- Starting Real-World Simulation: Portfolio Server ---")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Load Prices
            print("1. Loading Prices...")
            res = await session.call_tool("load_prices_csv", arguments={"file_path": csv_file})
            if res.isError:
                print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")
            else:
                print(" \033[92m[PASS]\033[0m Loaded")

            # Store prices_input (usually just the path or JSON string)
            # The tool `load_prices_csv` returns JSON string, which is `prices_input` for other tools?
            prices_input = res.content[0].text

            # 2. Expected Returns (Mean)
            print("2. Calculating Expected Returns...")
            res = await session.call_tool("mean_historical_return", arguments={"prices_input": prices_input})
            print(f" \033[92m[PASS]\033[0m Returns: {res.content[0].text}")

            # 2b. Risk Model (Sample Cov)
            print("2b. Risk Model (Sample Cov)...")
            res = await session.call_tool("sample_cov", arguments={"prices_input": prices_input})
            if not res.isError:
                print(" \033[92m[PASS]\033[0m Covariance calculated")

            # 2c. HRP Optimization
            print("2c. HRP Optimization...")
            res = await session.call_tool("hrp_optimize", arguments={"prices_input": prices_input})
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m HRP Weights: {res.content[0].text}")

            # 3. Optimize (Max Sharpe)
            print("3. Optimizing Max Sharpe...")
            res = await session.call_tool("ef_max_sharpe", arguments={"prices_input": prices_input})
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m Weights: {res.content[0].text}")

            # 4. Generate Report
            # Needs weights from step 3
            if not res.isError:
                import json
                try:
                    weights = json.loads(res.content[0].text)
                    print("4. Generating Report...")
                    res = await session.call_tool("generate_report", arguments={"prices_input": prices_input, "weights": weights})
                    if not res.isError:
                        report_path = res.content[0].text
                        print(f" \033[92m[PASS]\033[0m Report: {report_path}")
                        if os.path.exists(report_path):
                            try:
                                os.remove(report_path)
                            except Exception:
                                pass
                except Exception:
                    pass

    # Cleanup
    if os.path.exists(csv_file):
        try:
            os.remove(csv_file)
        except Exception:
            pass

    print("--- Portfolio Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
