import pytest

import asyncio
from mcp_servers.pdr_server.server import PdrServer

async def verify():
    print("--- Verifying Pandas Datareader (PDR) Server ---")
    server = PdrServer()
    tools = server.get_tools()
    print(f"Total Tools Registered: {len(tools)}")
    
    # Test 1: Academic (Fama-French)
    print("\n--- Testing Fama-French: Daily Factors ---")
    try:
        handler = server._handlers["get_ff_factors_daily"]
        res = await handler({})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:300])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Exception: {e}")

    # Test 2: Market (Stooq) - US 10Y Bond Yield
    print("\n--- Testing Stooq: US 10Y Bond (10USY.B) ---")
    try:
        handler = server._handlers["get_stooq_data"]
        res = await handler({"symbols": ["10USY.B"]}) # Stooq code for 10Y Yield
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:300])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")

    # Test 3: Dashboard (Factors)
    print("\n--- Testing Dashboard: Academic Factors ---")
    try:
        handler = server._handlers["get_factor_dashboard"]
        res = await handler({})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:300])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")

    # Test 4: Phase 2 Nasdaq Symbols
    print("\n--- Testing Nasdaq Symbols (Query='Apple') ---")
    try:
        handler = server._handlers["get_nasdaq_symbol_list"]
        res = await handler({"query": "Apple"})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:300])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")

    # Test 5: Phase 2 Bank of Canada
    print("\n--- Testing Bank of Canada (FXUSDCAD) ---")
    try:
        handler = server._handlers["get_bank_of_canada_data"]
        res = await handler({"symbols": ["FXUSDCAD"], "start_date": "2023-01-01"})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:300])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")

    except Exception as e:
         print(f"Exception: {e}")

    # Test 6: Phase 3 Industry Dashboard
    print("\n--- Testing Industry Health (49 Industries) ---")
    try:
        handler = server._handlers["get_industry_health_dashboard"]
        res = await handler({})
        if not res.isError:
             print("SUCCESS snippet:\n", res.content[0].text[:300])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
         print(f"Exception: {e}")
         
    # Test 7: Phase 3 Tiingo (Expect Error without Key)
    print("\n--- Testing Tiingo (No Key) ---")
    try:
        handler = server._handlers["get_tiingo_data"]
        # Should return strict error message
        res = await handler({"symbols": "AAPL"})
        if res.isError:
             print("SUCCESS: Gracefully failed as expected:\n", res.content[0].text)
        else:
             print("FAILED: Should have errored without key.")
    except Exception as e:
         print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(verify())


@pytest.mark.asyncio
async def test_main():
    await verify()

