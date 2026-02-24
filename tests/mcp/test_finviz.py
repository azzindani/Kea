
import pytest
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import SafeClientSession as ClientSession
from tests.mcp.client_utils import get_server_params


@pytest.mark.asyncio
async def test_finviz_real_simulation():
    """
    REAL SIMULATION: Verify Finviz Server (Screener, News, Quotes).
    """
    params = get_server_params("finviz_server", extra_dependencies=["finvizfinance", "pandas", "lxml"])

    print("\n--- Starting Real-World Simulation: Finviz Server ---")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Screener (Top Gainers)
            print("1. Screening Top Gainers...")
            res = await session.call_tool("screen_top_gainers", arguments={"limit": 5})
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m Top Gainers: {res.content[0].text[:1000]}...")
            else:
                print(f" \033[91m[FAIL]\033[0m (Network might be blocked) {res.content[0].text}")

            # 2. Company Description (AAPL)
            print("2. Getting Description (AAPL)...")
            res = await session.call_tool("get_company_description", arguments={"ticker": "AAPL"})
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m Description: {res.content[0].text[:1000]}...")
            else:
                print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            # 3. News
            print("3. Getting News (TSLA)...")
            res = await session.call_tool("get_stock_news", arguments={"ticker": "TSLA"})
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m News: {res.content[0].text[:1000]}...")
            else:
                print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            # 4. Sector Performance
            print("4. Getting Sector Performance...")
            res = await session.call_tool("get_sector_performance")
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m Sectors: {res.content[0].text[:1000]}...")

            # 5. Crypto Performance
            print("5. Getting Crypto Performance...")
            res = await session.call_tool("get_crypto_performance")
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m Crypto: {res.content[0].text[:1000]}...")

            # 6. Technical Table
            print("6. Getting Technical Table (Limit 5)...")
            res = await session.call_tool("get_technical_table", arguments={"limit": 5})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Tech Table: {res.content[0].text[:1000]}...")

    print("--- Finviz Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
