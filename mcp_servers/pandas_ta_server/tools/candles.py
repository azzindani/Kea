

from mcp_servers.pandas_ta_server.tools.universal import calculate_indicator


# Wrappers for common candle patterns
async def calculate_cdl_doji(data: list[dict], params: dict = None) -> str:
    """Candle: Doji."""
    return await calculate_indicator(data, 'cdl_doji', params)

async def calculate_cdl_hammer(data: list[dict], params: dict = None) -> str:
    """Candle: Hammer."""
    return await calculate_indicator(data, 'cdl_hammer', params)

async def calculate_cdl_engulfing(data: list[dict], params: dict = None) -> str:
    """Candle: Engulfing."""
    return await calculate_indicator(data, 'cdl_engulfing', params)

async def calculate_cdl_morningstar(data: list[dict], params: dict = None) -> str:
    """Candle: Morning Star."""
    return await calculate_indicator(data, 'cdl_morningstar', params)

async def calculate_cdl_eveningstar(data: list[dict], params: dict = None) -> str:
    """Candle: Evening Star."""
    return await calculate_indicator(data, 'cdl_eveningstar', params)

