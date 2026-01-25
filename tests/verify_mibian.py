
import asyncio
from mcp_servers.mibian_server.server import MibianServer
import pandas as pd
import json

async def verify():
    server = MibianServer()
    print("--- Verifying Mibian Server ---")
    print(f"Total Tools: {len(server.get_tools())}")

    # 1. Test Bulk Option Chain
    print("\n--- 1. Testing Bulk Option Chain ---")
    chain_data = []
    # Create 5 options
    base_strike = 100
    for i in range(5):
        chain_data.append({
            "underlying": 100,
            "strike": base_strike + (i*5), # 100, 105, 110...
            "interest": 5, # 5%
            "days": 30,
            "volatility": 20, # 20%
            "model": "BS"
        })
        
    try:
        handler = server._handlers["price_option_chain"]
        res = await handler({"data": chain_data})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:500])
             # Check if prices are there
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 2. Test Single Pricing (BS)
    print("\n--- 2. Testing BS Pricing ---")
    try:
        handler = server._handlers["calculate_bs_price"]
        # U=100, K=100, R=5, D=30, Vol=20
        res = await handler({"underlying": 100, "strike": 100, "interest": 5, "days": 30, "volatility": 20})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:200])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 3. Test Greeks (Delta)
    print("\n--- 3. Testing BS Delta ---")
    try:
        handler = server._handlers["calculate_bs_delta"]
        res = await handler({"underlying": 100, "strike": 100, "interest": 5, "days": 30, "volatility": 20})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:200])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 4. Test Implied Volatility
    print("\n--- 4. Testing IV ---")
    try:
        # First get a price
        # From previous test, assume Call Price ~ 2.4 (just guessing, let's use a known value logic or feed back)
        # Let's verify IV calculation 
        handler = server._handlers["calculate_implied_volatility"]
        # If U=100, K=100, R=5, D=30. Call Price 5.
        res = await handler({"underlying": 100, "strike": 100, "interest": 5, "days": 30, "call_price": 2.28}) # Approx price for 20% vol
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:200])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 5. Test Advanced Greeks (Phase 3)
    print("\n--- 5. Testing Advanced Greeks (Vanna) ---")
    try:
        handler = server._handlers["calculate_vanna"]
        res = await handler({"underlying": 100, "strike": 100, "interest": 5, "days": 30, "volatility": 20})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:500])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 6. Test Binary Price (Phase 3)
    print("\n--- 6. Testing Binary Option ---")
    try:
        handler = server._handlers["calculate_binary_price"]
        res = await handler({"underlying": 100, "strike": 100, "interest": 5, "days": 30, "volatility": 20})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:200])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 7. Test American Price (Phase 4)
    print("\n--- 7. Testing American Option (BAW) ---")
    try:
        handler = server._handlers["calculate_american_price"]
        res = await handler({"underlying": 100, "strike": 100, "interest": 5, "days": 30, "volatility": 20})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:500])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # 8. Test Barrier Price (Phase 4)
    print("\n--- 8. Testing Barrier Option (Down-and-Out) ---")
    try:
        handler = server._handlers["calculate_barrier_price"]
        # Spot 100, Barrier 95. Should be cheaper than vanilla.
        res = await handler({"underlying": 100, "strike": 100, "interest": 5, "days": 30, "volatility": 20, "barrier": 95, "barrier_type": "down-and-out"})
        if not res.isError:
             print("SUCCESS snippet:", res.content[0].text[:500])
        else:
             print("FAILED:", res.content[0].text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
