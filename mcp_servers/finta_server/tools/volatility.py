

from mcp_servers.finta_server.tools.universal import calculate_indicator


async def calculate_atr(data: list[dict], params: dict = None) -> str:
    """ATR - Average True Range."""
    return await calculate_indicator(data, 'ATR', params)

async def calculate_bbands(data: list[dict], params: dict = None) -> str:
    """BBANDS - Bollinger Bands."""
    return await calculate_indicator(data, 'BBANDS', params)

async def calculate_kc(data: list[dict], params: dict = None) -> str:
    """KC - Keltner Channels."""
    return await calculate_indicator(data, 'KC', params)

async def calculate_do(data: list[dict], params: dict = None) -> str:
    """DO - Donchian Channels."""
    return await calculate_indicator(data, 'DO', params)

async def calculate_mobo(data: list[dict], params: dict = None) -> str:
    """MOBO - Momentum Breakout Bands."""
    return await calculate_indicator(data, 'MOBO', params)

async def calculate_tr(data: list[dict], params: dict = None) -> str:
    """TR - True Range."""
    return await calculate_indicator(data, 'TR', params)

async def calculate_bbwidth(data: list[dict], params: dict = None) -> str:
    """BBWIDTH - Bollinger Band Width."""
    return await calculate_indicator(data, 'BBWIDTH', params)

async def calculate_percent_b(data: list[dict], params: dict = None) -> str:
    """PERCENT_B - Percent B."""
    return await calculate_indicator(data, 'PERCENT_B', params)

async def calculate_apz(data: list[dict], params: dict = None) -> str:
    """APZ - Adaptive Price Zone."""
    return await calculate_indicator(data, 'APZ', params)

async def calculate_massi(data: list[dict], params: dict = None) -> str:
    """MASSI - Mass Index."""
    return await calculate_indicator(data, 'MASSI', params)

