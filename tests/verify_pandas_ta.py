
import asyncio
import pandas as pd
from mcp_servers.pandas_ta_server.server import PandasTAServer

async def verify():
    print("--- Verifying Pandas TA Server ---")
    server = PandasTAServer()
    print(f"Total Tools: {len(server.get_tools())}")
    
    # Dummy Data (5 days)
    data = [
        {"date": "2023-01-01", "open": 100, "high": 110, "low": 90, "close": 105, "volume": 1000},
        {"date": "2023-01-02", "open": 105, "high": 115, "low": 95, "close": 110, "volume": 1500},
        {"date": "2023-01-03", "open": 110, "high": 120, "low": 100, "close": 115, "volume": 1200},
        {"date": "2023-01-04", "open": 115, "high": 125, "low": 105, "close": 120, "volume": 1800},
        {"date": "2023-01-05", "open": 120, "high": 130, "low": 110, "close": 125, "volume": 2000}
    ]
    
    # 1. Test SMA (Trend)
    print("\n--- 1. Testing SMA (Trend) ---")
    try:
        handler = server._handlers["calculate_sma"]
        res = await handler({"data": data, "params": {"length": 2}})
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
        res = await handler({"data": data, "params": {"length": 2}})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:200])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 3. Test Bulk (Momentum Suite)
    print("\n--- 3. Testing Momentum Suite (Bulk) ---")
    try:
        handler = server._handlers["get_momentum_suite"]
        # Need more data for some indicators, but let's try
        # expanding data to 20 days for safety?
        long_data = data * 4 
        # fix dates? pandas_ta might handle duplicates or index reset. core.py handles it.
        
        res = await handler({"data": long_data})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:200])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")
        
    # 4. Test Candle Patterns (Phase 2)
    print("\n--- 4. Testing Candle Patterns (Phase 2) ---")
    try:
        handler = server._handlers["get_candle_patterns_suite"]
        res = await handler({"data": long_data})
        if not res.isError:
             print("SUCCESS snippet (Candles):", res.content[0].text[:200])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 5. Test Signal Generator (Phase 2 - Logic)
    print("\n--- 5. Testing Signal Generator (Logic) ---")
    try:
        handler = server._handlers["generate_signals"]
        # Condition: RSI < 50 (Since using dummy data, might vary, but simplified)
        # Note: RSI_14 is default name usually.
        res = await handler({"data": long_data, "condition": "close > 10"}) 
        if not res.isError:
             print("SUCCESS snippet (Signals):", res.content[0].text[:200])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 6. Test Performance (Phase 3)
    print("\n--- 6. Testing Performance (Drawdown) ---")
    try:
        handler = server._handlers["calculate_drawdown"]
        res = await handler({"data": long_data})
        if not res.isError:
             print("SUCCESS snippet (Drawdown):", res.content[0].text[:200])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 7. Test ML Dataset (Phase 4)
    print("\n--- 7. Testing ML Dataset Construction ---")
    try:
        handler = server._handlers["construct_ml_dataset"]
        res = await handler({"data": long_data, "lags": [1, 2], "target_horizon": 1})
        if not res.isError:
             print("SUCCESS snippet (ML):", res.content[0].text[:200])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 8. Test Spectral (Phase 5)
    print("\n--- 8. Testing Spectral (Fisher) ---")
    try:
        handler = server._handlers["calculate_fisher"]
        res = await handler({"data": long_data})
        if not res.isError:
             print("SUCCESS snippet (Fisher):", res.content[0].text[:200])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
