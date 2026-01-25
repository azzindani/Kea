
import asyncio
from mcp_servers.finviz_server.server import FinvizServer

async def verify():
    print("--- Verifying Finviz Server ---")
    server = FinvizServer()
    tools = server.get_tools()
    print(f"Total Tools Registered: {len(tools)}")
    
    # Test 1: Screener Signal (Top Gainers)
    print("\n--- Testing Signal: Top Gainers ---")
    try:
        handler = server._handlers["screen_top_gainers"]
        res = await handler({"limit": 5})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:300])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Exception: {e}")

    # Test 2: Quote (Ratings) - Requires Ticker
    print("\n--- Testing Quote: Ratings (TSLA) ---")
    try:
        handler = server._handlers["get_stock_ratings"]
        res = await handler({"ticker": "TSLA"})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:300])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")

    # Test 3: Groups (Sector Performance)
    print("\n--- Testing Groups: Sector Performance ---")
    try:
        handler = server._handlers["get_sector_performance"]
        res = await handler({})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:300])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")

    # Test 4: Insider (Latest Buys)
    print("\n--- Testing Insider: Latest Buys ---")
    try:
        handler = server._handlers["get_latest_buys"]
        res = await handler({})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:300])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")

    # Test 5: Phase 2 Global (Forex)
    print("\n--- Testing Global: Forex Performance ---")
    try:
        handler = server._handlers["get_forex_performance"]
        res = await handler({})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:300])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")
         
    # Test 6: Phase 2 Strategy (Value Stocks)
    print("\n--- Testing Strategy: Value Stocks ---")
    try:
        handler = server._handlers["screen_strat_value_stocks"]
        res = await handler({"limit": 3})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:300])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")

    # Test 7: Phase 3 Chart URL
    print("\n--- Testing Chart URL (AAPL) ---")
    try:
        handler = server._handlers["get_chart_url"]
        res = await handler({"ticker": "AAPL"})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text)
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")
         
    # Test 8: Phase 3 Bulk TA
    print("\n--- Testing Bulk TA Table ---")
    try:
        handler = server._handlers["get_technical_table"]
        res = await handler({"limit": 3})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:300])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
