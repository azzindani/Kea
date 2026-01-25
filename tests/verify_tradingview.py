
import asyncio
import json
from mcp_servers.tradingview_server.server import TradingViewServer

async def verify_server():
    print("--- Verifying TradingView Server ---")
    server = TradingViewServer()
    tools = server.get_tools()
    print(f"Total Tools Registered: {len(tools)}")
    
    # Test 1: TA Summary
    print("\n--- Testing TA Summary (AAPL) ---")
    handler = server._handlers["get_ta_summary"]
    res = await handler({"symbol": "AAPL", "screener": "america", "exchange": "NASDAQ", "interval": "1d"})
    if not res.isError:
        print("SUCCESS:", res.content[0].text[:200])
    else:
        print("FAILED:", res.content[0].text)

    # Test 2: Screener
    print("\n--- Testing Screener (Top Gainers US) ---")
    handler = server._handlers["scan_america_top_gainers"]
    res = await handler({"limit": 5})
    if not res.isError:
        print("SUCCESS (Rows):", len(json.loads(res.content[0].text)))
    else:
        print("FAILED:", res.content[0].text)
        
    # Test 3: Bulk Data
    print("\n--- Testing Bulk Data (AAPL, TSLA) ---")
    handler = server._handlers["get_bulk_data"]
    res = await handler({"tickers": ["NASDAQ:AAPL", "NASDAQ:TSLA"], "columns": ["close", "RSI"], "market": "america"})
    if not res.isError:
        print("SUCCESS:", res.content[0].text)
    else:
        print("FAILED:", res.content[0].text)

    # Test 4: Phase 2 Fundamentals
    print("\n--- Testing Fundamentals (AAPL: P/E) ---")
    handler = server._handlers["get_tv_price_earnings"]
    res = await handler({"ticker": "NASDAQ:AAPL"})
    if not res.isError:
        print("SUCCESS (P/E):", res.content[0].text)
    else:
        print("FAILED:", res.content[0].text)

    # Test 5: Phase 2 Performance
    print("\n--- Testing Performance (AAPL: 1M Change) ---")
    handler = server._handlers["get_perf_1m"]
    res = await handler({"ticker": "NASDAQ:AAPL"})
    if not res.isError:
        print("SUCCESS (1M):", res.content[0].text)
    else:
        print("FAILED:", res.content[0].text)

if __name__ == "__main__":
    asyncio.run(verify_server())
