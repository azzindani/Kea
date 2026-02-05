

from mcp_servers.pandas_ta_server.tools.universal import calculate_indicator


async def calculate_rsx(data: list[dict], params: dict = None) -> str:
    """Calculates Relative Strength Xtra (Jurik RSI). Smoother."""
    return await calculate_indicator(data, 'rsx', params)

async def calculate_thermo(data: list[dict], params: dict = None) -> str:
    """Calculates Elder's Thermometer (Volatility)."""
    return await calculate_indicator(data, 'thermo', params)

async def calculate_massi(data: list[dict], params: dict = None) -> str:
    """Calculates Mass Index (Reversal)."""
    return await calculate_indicator(data, 'massi', params)

async def calculate_ui(data: list[dict], params: dict = None) -> str:
    """Calculates Ulcer Index (Downside Risk)."""
    return await calculate_indicator(data, 'ui', params)

async def calculate_natr(data: list[dict], params: dict = None) -> str:
    """Calculates Normalized ATR."""
    return await calculate_indicator(data, 'natr', params)

