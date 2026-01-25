
import asyncio
from mcp_servers.finta_server.server import FintaServer
import pandas as pd
import json

async def verify():
    server = FintaServer()
    print("--- Verifying Finta Server ---")
    print(f"Total Tools: {len(server.get_tools())}")

    # Dummy Data (List of Dicts)
    # Finta needs: open, high, low, close, volume (lowercase)
    data = []
    prices = [100, 105, 110, 115, 112, 108, 105, 102, 100, 98, 95, 92, 90, 95, 100]
    for i, p in enumerate(prices):
        data.append({
            "date": f"2023-01-{i+1:02d}",
            "open": p - 2,
            "high": p + 5,
            "low": p - 5,
            "close": p,
            "volume": 1000 + (i * 100)
        })

    # 1. Test SMA (Trend)
    print("\n--- 1. Testing SMA (Trend) ---")
    try:
        handler = server._handlers["calculate_sma"]
        # Default period often 41 but works on small data?
        # Let's pass params.
        res = await handler({"data": data, "params": {"period": 3}})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:200])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 2. Test RSI (Momentum)
    print("\n--- 2. Testing RSI (Momentum) ---")
    try:
        handler = server._handlers["calculate_rsi"]
        res = await handler({"data": data, "params": {"period": 3}})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:200])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 3. Test Bulk Momentum Suite
    print("\n--- 3. Testing Momentum Suite (Bulk) ---")
    try:
        handler = server._handlers["get_momentum_suite"]
        res = await handler({"data": data})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:200])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 4. Test Universal Tool
    print("\n--- 4. Testing Universal Tool (ATR) ---")
    try:
        handler = server._handlers["calculate_indicator"]
        res = await handler({"data": data, "indicator": "ATR", "params": {"period": 3}})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:200])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 5. Test Exotics (Phase 2)
    print("\n--- 5. Testing Exotics (WTO) ---")
    try:
        handler = server._handlers["calculate_wto"]
        res = await handler({"data": data})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:200])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 6. Test Levels (Phase 2)
    print("\n--- 6. Testing Levels (Pivot) ---")
    try:
        handler = server._handlers["calculate_pivot"]
        res = await handler({"data": data})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:200])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")
        
    # 7. Test Clouds (Phase 3)
    print("\n--- 7. Testing Clouds (Ichimoku) ---")
    try:
        handler = server._handlers["calculate_ichimoku"]
        res = await handler({"data": data})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:200])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 8. Test Weighted (Phase 4)
    print("\n--- 8. Testing Weighted (VWAP) ---")
    try:
        handler = server._handlers["calculate_vwap"]
        res = await handler({"data": data})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:200])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")
        
    # 9. Test Exits (Phase 4)
    print("\n--- 9. Testing Exits (Chandelier) ---")
    try:
        handler = server._handlers["calculate_chandelier"]
        res = await handler({"data": data})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:200])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
