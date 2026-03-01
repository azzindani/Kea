
import pytest
from mcp import ClientSession
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import get_server_params


@pytest.mark.asyncio
async def test_yahooquery_real_simulation():
    """
    REAL SIMULATION: Verify YahooQuery Server (Finance).
    """
    params = get_server_params("yahooquery_server", extra_dependencies=["yahooquery", "pandas"])

    ticker = "MSFT"

    print("\n--- Starting Real-World Simulation: YahooQuery Server ---")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Get Fundamental Snapshot
            print(f"1. Fetching Snapshot for {ticker}...")
            res = await session.call_tool("get_fundamental_snapshot", arguments={"tickers": ticker})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Snapshot Data Length: {len(res.content[0].text)}")

            # 2. Search Ticker
            print("2. Searching for 'Tesla'...")
            res = await session.call_tool("search_ticker", arguments={"query": "Tesla"})
            print(f" \033[92m[PASS]\033[0m Results: {res.content[0].text}")

            # 3. Trending Symbols
            print("3. Getting Trending Symbols...")
            res = await session.call_tool("get_trending_symbols", arguments={"country": "united states", "count": 3})
            print(f" \033[92m[PASS]\033[0m Trending: {res.content[0].text}")

            # 4. Income Statement
            print("4. Getting Income Statement...")
            res = await session.call_tool("get_income_statement", arguments={"ticker": ticker})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Income Stmt Rows: {len(res.content[0].text)}")

            # 5. Balance Sheet
            print("5. Getting Balance Sheet...")
            res = await session.call_tool("get_balance_sheet", arguments={"ticker": ticker})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Balance Sheet Rows: {len(res.content[0].text)}")

    print("--- YahooQuery Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
