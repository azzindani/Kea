
import pytest
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import SafeClientSession as ClientSession
from tests.mcp.client_utils import get_server_params


@pytest.mark.asyncio
async def test_pdr_real_simulation():
    """
    REAL SIMULATION: Verify PDR Server (Pandas DataReader).
    """
    params = get_server_params("pdr_server", extra_dependencies=["pandas_datareader", "pandas", "setuptools"])

    print("\n--- Starting Real-World Simulation: PDR Server ---")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Fama-French
            print("1. Fetching Fama-French Data (F-F_Research_Data_Factors)...")
            res = await session.call_tool("get_fama_french_data", arguments={"dataset_name": "F-F_Research_Data_Factors"})
            if not res.isError:
                 print(" \033[92m[PASS]\033[0m Data received")
            else:
                 print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            # 2. Stooq (AAPL)
            print("2. Fetching Stooq Data (AAPL.US)...")
            # Stooq often uses .US suffix
            res = await session.call_tool("get_stooq_data", arguments={"symbols": ["AAPL.US"]})
            if not res.isError:
                 print(" \033[92m[PASS]\033[0m Data received")
            else:
                 print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            # 3. NASDAQ Symbols
            print("3. Searching NASDAQ Symbols...")
            res = await session.call_tool("get_nasdaq_symbol_list", arguments={"query": "Apple"})
            if not res.isError:
                 print(" \033[92m[PASS]\033[0m Symbols found")

            # 4. Factor Dashboard
            print("4. Fetching Factor Dashboard...")
            res = await session.call_tool("get_factor_dashboard")
            if not res.isError:
                 print(" \033[92m[PASS]\033[0m Dashboard data received")

    print("--- PDR Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
