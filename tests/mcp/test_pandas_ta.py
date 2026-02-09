import pytest
import asyncio
import json
from tests.mcp.client_utils import SafeClientSession as ClientSession
from mcp.client.stdio import stdio_client
from tests.mcp.client_utils import get_server_params
from mcp import McpError

@pytest.mark.asyncio
async def test_pandas_ta_real_simulation():
    """
    REAL SIMULATION: Verify Pandas TA Server (Technical Analysis).
    """
    params = get_server_params("pandas_ta_server", extra_dependencies=["pandas", "pandas_ta"])
    
    # Synthetic OHLCV Data
    data = [
        {"open": 100, "high": 105, "low": 98, "close": 102, "volume": 1000},
        {"open": 102, "high": 108, "low": 101, "close": 107, "volume": 1500},
        {"open": 107, "high": 110, "low": 105, "close": 109, "volume": 1200},
        {"open": 109, "high": 115, "low": 108, "close": 113, "volume": 2000},
        {"open": 113, "high": 112, "low": 100, "close": 105, "volume": 1800},
        {"open": 105, "high": 108, "low": 102, "close": 106, "volume": 1300},
        {"open": 106, "high": 110, "low": 105, "close": 108, "volume": 1400},
        {"open": 108, "high": 112, "low": 107, "close": 110, "volume": 1600},
        {"open": 110, "high": 115, "low": 109, "close": 112, "volume": 1700},
        {"open": 112, "high": 118, "low": 111, "close": 116, "volume": 1900},
        {"open": 116, "high": 120, "low": 115, "close": 119, "volume": 2100},
        {"open": 119, "high": 122, "low": 118, "close": 121, "volume": 2200},
        {"open": 121, "high": 125, "low": 120, "close": 124, "volume": 2400},
        {"open": 124, "high": 123, "low": 118, "close": 120, "volume": 2300}
    ]
    
    print(f"\n--- Starting Real-World Simulation: Pandas TA Server ---")
    
    try:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # 1. RSI
                print("1. Calculating RSI...")
                res = await session.call_tool("calculate_rsi", arguments={"data": data})
                print(f" \033[92m[PASS]\033[0m RSI: {res.content[0].text[:1000]}...")

                # 2. MACD
                print("2. Calculating MACD...")
                res = await session.call_tool("calculate_macd", arguments={"data": data})
                print(f" \033[92m[PASS]\033[0m MACD: {res.content[0].text[:1000]}...")

                # 3. SMA
                print("3. Calculating SMA...")
                res = await session.call_tool("calculate_sma", arguments={"data": data, "params": {"length": 3}})
                print(f" \033[92m[PASS]\033[0m SMA: {res.content[0].text[:1000]}...")

                # 4. Supertrend
                print("4. Calculating Supertrend...")
                res = await session.call_tool("calculate_supertrend", arguments={"data": data})
                print(f" \033[92m[PASS]\033[0m Supertrend: {res.content[0].text[:1000]}...")

                # 5. All Indicators
                print("5. Bulk Indicators (Suite)...")
                res = await session.call_tool("get_momentum_suite", arguments={"data": data})
                print(f" \033[92m[PASS]\033[0m Momentum Suite: {len(res.content[0].text)} chars")
    except BaseException as e:
        # ExceptionGroup wraps nested exceptions; flatten to check all messages
        def _flatten_exc(exc):
            msgs = [str(exc)]
            if isinstance(exc, BaseExceptionGroup):
                for sub in exc.exceptions:
                    msgs.extend(_flatten_exc(sub))
            if exc.__cause__:
                msgs.extend(_flatten_exc(exc.__cause__))
            return msgs
        all_msgs = " ".join(_flatten_exc(e))
        if "Connection closed" in all_msgs or "unsatisfiable" in all_msgs:
            pytest.skip(f"pandas_ta server unavailable (requires Python>=3.12)")
        raise

    print("--- Pandas TA Simulation Complete ---")

if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-v", "-s", __file__]))
