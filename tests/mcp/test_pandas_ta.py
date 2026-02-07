import pytest
import asyncio
import pandas as pd
from mcp_servers.pandas_ta_server.server import PandasTAServer

@pytest.mark.asyncio
async def test_pandas_ta_tools():
    """Verify Pandas TA Server indicators."""
    server = PandasTAServer()
    
    # Dummy Data (5 days)
    data = [
        {"date": "2023-01-01", "open": 100, "high": 110, "low": 90, "close": 105, "volume": 1000},
        {"date": "2023-01-02", "open": 105, "high": 115, "low": 95, "close": 110, "volume": 1500},
        {"date": "2023-01-03", "open": 110, "high": 120, "low": 100, "close": 115, "volume": 1200},
        {"date": "2023-01-04", "open": 115, "high": 125, "low": 105, "close": 120, "volume": 1800},
        {"date": "2023-01-05", "open": 120, "high": 130, "low": 110, "close": 125, "volume": 2000}
    ]
    # Expand data for more indicators
    long_data = data * 4 

    # 1. SMA
    handler = server._handlers["calculate_sma"]
    res = await handler({"data": data, "params": {"length": 2}})
    assert not res.isError
    assert "SMA" in res.content[0].text

    # 2. RSI
    handler = server._handlers["calculate_rsi"]
    res = await handler({"data": data, "params": {"length": 2}})
    assert not res.isError
    assert "RSI" in res.content[0].text

    # 3. Momentum Suite
    handler = server._handlers["get_momentum_suite"]
    res = await handler({"data": long_data})
    assert not res.isError
    assert "RSI" in res.content[0].text

    # 4. Signal Generator
    handler = server._handlers["generate_signals"]
    res = await handler({"data": long_data, "condition": "close > 10"})
    assert not res.isError
    assert "Signal" in res.content[0].text
    
    # 5. ML Dataset
    handler = server._handlers["construct_ml_dataset"]
    res = await handler({"data": long_data, "lags": [1], "target_horizon": 1})
    assert not res.isError
    assert "target" in res.content[0].text.lower()
