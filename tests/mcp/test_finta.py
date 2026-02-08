import pytest
import asyncio
from tests.mcp.client_utils import SafeClientSession as ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params

@pytest.mark.asyncio
async def test_finta_real_simulation():
    """
    REAL SIMULATION: Verify Finta Server (Technical Indicators) with synthetic data.
    """
    params = get_server_params("finta_server", extra_dependencies=["finta", "pandas"])
    
    # Synthetic Data (OHLCV)
    data = [
        {"open": 10, "high": 12, "low": 9, "close": 11, "volume": 100},
        {"open": 11, "high": 13, "low": 10, "close": 12, "volume": 110},
        {"open": 12, "high": 14, "low": 11, "close": 13, "volume": 120},
        {"open": 13, "high": 15, "low": 12, "close": 14, "volume": 130},
        {"open": 14, "high": 16, "low": 13, "close": 15, "volume": 140},
        {"open": 15, "high": 17, "low": 14, "close": 14, "volume": 150}, # Downtick
        {"open": 14, "high": 15, "low": 13, "close": 13, "volume": 160},
    ]
    
    print(f"\n--- Starting Real-World Simulation: Finta Server ---")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 1. RSI
            print("1. Calculating RSI...")
            res = await session.call_tool("calculate_rsi", arguments={"data": data})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m RSI Data: {res.content[0].text[:1000]}...")
            else:
                 print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

            # 2. SMA
            print("2. Calculating SMA...")
            res = await session.call_tool("calculate_sma", arguments={"data": data})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m SMA Data: {res.content[0].text[:1000]}...")

            # 3. Bollinger Bands
            print("3. Calculating Bollinger Bands...")
            res = await session.call_tool("calculate_bbands", arguments={"data": data})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m BBands Data: {res.content[0].text[:1000]}...")
            
            # 4. Ichimoku (Cloud)
            print("4. Calculating Ichimoku (Cloud)...")
            res = await session.call_tool("calculate_ichimoku", arguments={"data": data})
            if not res.isError:
                 print(f" \033[92m[PASS]\033[0m Ichimoku Data: {res.content[0].text[:1000]}...")

            # 5. Bulk All
            print("5. Calculating ALL Indicators (Bulk)...")
            res = await session.call_tool("get_all_indicators", arguments={"data": data})
            if not res.isError:
                print(f" \033[92m[PASS]\033[0m Bulk Result Length: {len(res.content[0].text)}")
            else:
                print(f" \033[91m[FAIL]\033[0m {res.content[0].text}")

    print("--- Finta Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
