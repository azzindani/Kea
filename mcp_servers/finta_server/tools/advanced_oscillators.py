

from mcp_servers.finta_server.tools.universal import calculate_indicator


async def calculate_trix(data: list[dict], params: dict = None) -> str:
    """TRIX - Triple Exponential Average Oscillator."""
    return await calculate_indicator(data, 'TRIX', params)

async def calculate_ift_rsi(data: list[dict], params: dict = None) -> str:
    """IFT_RSI - Inverse Fisher Transform RSI."""
    return await calculate_indicator(data, 'IFT_RSI', params)

async def calculate_sqzmi(data: list[dict], params: dict = None) -> str:
    """SQZMI - Squeeze Momentum Indicator."""
    return await calculate_indicator(data, 'SQZMI', params)

async def calculate_mi(data: list[dict], params: dict = None) -> str:
    """MI - Mass Index (Standard)."""
    return await calculate_indicator(data, 'MI', params)

