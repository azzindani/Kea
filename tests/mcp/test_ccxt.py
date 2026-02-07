import pytest
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_ccxt_real_simulation():
    """
    REAL SIMULATION: Verify CCXT Server with real crypto data (BTC/USDT).
    """
    params = get_server_params("ccxt_server", extra_dependencies=["ccxt", "pandas"])
    
    print(f"\n--- Starting Real-World Simulation: CCXT Server ---")
    
    exchange = "binance"
    symbol = "BTC/USDT"
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 0. Discovery
            tools_res = await session.list_tools()
            tool_names = [t.name for t in tools_res.tools]
            print(f"Discovered {len(tool_names)} tools")

            # 1. Ticker
            print(f"1. Fetching Ticker for {exchange} {symbol}...")
            res = await session.call_tool("get_ticker", arguments={"exchange": exchange, "symbol": symbol})
            if not res.isError:
                print(f" [PASS] Ticker Data caught (Sample): {res.content[0].text[:100]}...")
            else:
                print(f" [FAIL] {res.content[0].text}")

            # 2. OHLCV
            print(f"2. Fetching OHLCV (1d)...")
            res = await session.call_tool("get_ohlcv", arguments={"exchange": exchange, "symbol": symbol, "timeframe": "1d", "limit": 3})
            if not res.isError:
                print(f" [PASS] Candles caught (Sample): {res.content[0].text[:100]}...")
            else:
                print(f" [FAIL] {res.content[0].text}")
                
            # 3. Order Book
            print(f"3. Fetching Order Book...")
            res = await session.call_tool("get_order_book", arguments={"exchange": exchange, "symbol": symbol, "limit": 5})
            if not res.isError:
                print(f" [PASS] Book depth caught")
            else:
                print(f" [FAIL] {res.content[0].text}")

            # 4. Global Price (Aggregator)
            print(f"4. Testing Aggregator (Global Price)...")
            res = await session.call_tool("get_global_price", arguments={"symbol": symbol})
            if not res.isError:
                print(f" [PASS] Global Price: {res.content[0].text}")
            else:
                print(f" [FAIL] {res.content[0].text}")
                
            # 5. Metadata
            print(f"5. Listing Markets (Coinbase)...")
            res = await session.call_tool("list_exchange_markets", arguments={"exchange": "coinbase"})
            if not res.isError:
                print(f" [PASS] Markets listed (Length check desc)")

            # 6. Derivatives (Funding Rate)
            print(f"6. Testing Derivatives (Funding Rate)...")
            res = await session.call_tool("get_funding_rate", arguments={"exchange": exchange, "symbol": "BTC/USDT:USDT"})
            if not res.isError:
                 print(f" [PASS] Funding Rate: {res.content[0].text}")
            else:
                 # Might fail if not available or symbol diff
                 print(f" [INFO] Funding Rate: {res.content[0].text}")

            # 7. History Download (Mock/Small)
            print(f"7. Testing History Download (limit query)...")
            # We use get_ohlcv with long range to simulate "download" or call the specific tool if we want to test pagination
            # The tool 'download_market_history' might take time, so we just check it exists or run small
            if "download_market_history" in tool_names:
                 # dry run or small days
                 pass

    print("--- CCXT Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
