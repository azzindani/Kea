import pytest

import asyncio
import json
from mcp_servers.yahooquery_server.server import YahooQueryServer

async def verify_server():
    print("--- Verifying YahooQuery Server ---")
    server = YahooQueryServer()
    tools = server.get_tools()
    print(f"Total Tools Registered: {len(tools)}")
    
    # Test 1: Bulk Ticker Attribute (Asset Profile)
    print("\n--- Testing Bulk Asset Profile (AAPL, MSFT) ---")
    try:
        handler = server._handlers["get_bulk_asset_profile"]
        res = await handler({"tickers": ["AAPL", "MSFT"]})
        if not res.isError:
            print("SUCCESS (Length):", len(res.content[0].text))
            print("Snippet:", res.content[0].text[:200])
        else:
            print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Exception: {e}")

    # Test 2: Screener (Day Gainers)
    print("\n--- Testing Screener (Day Gainers) ---")
    try:
        handler = server._handlers["screen_day_gainers"]
        res = await handler({"count": 5})
        if not res.isError:
            print("SUCCESS (Snippet):", res.content[0].text[:200])
        else:
            print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Exception: {e}")
        
    # Test 3: Multi-Talent (Fundamental Snapshot)
    print("\n--- Testing Multi-Talent (Fundamental Snapshot) ---")
    try:
        handler = server._handlers["get_fundamental_snapshot"]
        res = await handler({"tickers": ["GOOG"]})
        if not res.isError:
             print("SUCCESS:", res.content[0].text[:200])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Exception: {e}")

    # Test 4: History
    print("\n--- Testing Bulk History (AAPL, MSFT) ---")
    try:
        handler = server._handlers["get_history_bulk"]
        res = await handler({"tickers": ["AAPL", "MSFT"], "period": "5d"})
        if not res.isError:
             print("SUCCESS:", res.content[0].text)
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Exception: {e}")

    # Test 5: Phase 2 Financials (Balance Sheet)
    print("\n--- Testing Bulk Balance Sheet (Annual) ---")
    try:
        handler = server._handlers["get_bulk_balance_sheet_annual"]
        res = await handler({"tickers": ["AAPL"]})
        if not res.isError:
             print("SUCCESS (Snippet):", res.content[0].text[:100])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Exception: {e}")

    # Test 6: Market Intelligence
    print("\n--- Testing Market Trending (US) ---")
    try:
        handler = server._handlers["get_market_trending"]
        res = await handler({"country": "US", "count": 3})
        if not res.isError:
             print("SUCCESS:", res.content[0].text)
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Exception: {e}")

    # Test 7: Phase 3 Sector Screener
    print("\n--- Testing Sector Screener (Technology) ---")
    try:
        handler = server._handlers["screen_sector_technology"]
        res = await handler({"count": 3})
        if not res.isError:
             print("SUCCESS:", res.content[0].text[:100])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Exception: {e}")
        
    # Test 8: Phase 3 Special List
    print("\n--- Testing Special List (Most Shorted) ---")
    try:
        handler = server._handlers["screen_most_shorted_stocks"]
        res = await handler({"count": 3})
        if not res.isError:
             print("SUCCESS:", res.content[0].text[:100])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Exception: {e}")

    # Test 9: Phase 4 Funds (SPY Holdings)
    print("\n--- Testing Fund Holdings (SPY) ---")
    try:
        handler = server._handlers["get_fund_holdings"]
        res = await handler({"tickers": ["SPY"]})
        if not res.isError:
             print("SUCCESS (Snippet):", res.content[0].text[:200])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Exception: {e}")

    # Test 10: Phase 4 Discovery (Search Gold)
    print("\n--- Testing Search (Gold) ---")
    try:
        handler = server._handlers["search_instruments"]
        res = await handler({"query": "gold"})
        if not res.isError:
             print("SUCCESS (Snippet):", res.content[0].text[:200])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(verify_server())


@pytest.mark.asyncio
async def test_main():
    await verify()

