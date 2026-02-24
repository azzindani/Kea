
import pytest
from mcp import ClientSession
from mcp.client.stdio import stdio_client

from tests.mcp.client_utils import get_server_params


@pytest.mark.asyncio
async def test_tradingview_real_simulation():
    """
    REAL SIMULATION: Verify TradingView Server (TA/Screener).
    """
    params = get_server_params("tradingview_server", extra_dependencies=["tradingview_ta", "requests"])

    symbol = "AAPL"

    print("\n--- Starting Real-World Simulation: TradingView Server ---")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. TA Summary
            print(f"1. Getting TA Summary for {symbol}...")
            res = await session.call_tool("get_ta_summary", arguments={"symbol": symbol, "exchange": "NASDAQ", "interval": "1d"})
            print(f" \033[92m[PASS]\033[0m Summary: {res.content[0].text}")

            # 2. Get Fundamental (P/E)
            print(f"2. Getting P/E for {symbol}...")
            res = await session.call_tool("get_tv_price_earnings", arguments={"ticker": symbol})
            print(f" \033[92m[PASS]\033[0m P/E: {res.content[0].text}")

            # 3. Market Scan (Top Gainers)
            print("3. Scanning Top Gainers...")
            res = await session.call_tool("scan_america_top_gainers", arguments={"limit": 5})
            print(f" \033[92m[PASS]\033[0m Gainers: {res.content[0].text}")

    print("--- TradingView Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
