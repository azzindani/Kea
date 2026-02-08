import pytest
import asyncio
from tests.mcp.client_utils import SafeClientSession as ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_data_sources_real_simulation():
    """
    REAL SIMULATION: Verify Data Sources Server (Yahoo, FRED, World Bank).
    """
    params = get_server_params("data_sources_server", extra_dependencies=["yfinance", "fredapi", "wbgapi", "pandas"])
    
    print(f"\n--- Starting Real-World Simulation: Data Sources Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. Yahoo Finance
            print("1. Yahoo Finance (AAPL)...")
            res = await session.call_tool("yfinance_fetch", arguments={"symbol": "AAPL", "period": "1mo"})
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m YFinance Data: {res.content[0].text[:1000]}...")
            else:
                print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            # 2. FRED (GDP)
            print("2. FRED (GDP - GNPCA)...")
            res = await session.call_tool("fred_fetch", arguments={"series_id": "GNPCA"})
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m FRED Data: {res.content[0].text[:1000]}...")
            else:
                # API Key might be missing in env, so expect potential fail but check handling
                print(f" [INFO] FRED Result: {res.content[0].text[:1000]}")

            # 3. World Bank (GDP)
            print("3. World Bank (NY.GDP.MKTP.CD for US)...")
            res = await session.call_tool("world_bank_fetch", arguments={"indicator": "NY.GDP.MKTP.CD", "country": "US", "start_year": 2020})
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m World Bank Data: {res.content[0].text[:1000]}...")
            else:
                print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")
                
            # 4. CSV Fetch
            print("4. CSV Fetch (Iris Dataset)...")
            url = "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv"
            res = await session.call_tool("csv_fetch", arguments={"url": url})
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m CSV Preview:\n{res.content[0].text[:1000]}...")
            else:
                print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

    print("--- Data Sources Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
