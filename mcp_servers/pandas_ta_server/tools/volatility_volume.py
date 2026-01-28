

from mcp_servers.pandas_ta_server.tools.universal import calculate_indicator


# Volatility
async def calculate_bbands(data: list[dict], params: dict = None) -> str:
    """Bollinger Bands."""
    return await calculate_indicator(data, 'bbands', params)

async def calculate_atr(data: list[dict], params: dict = None) -> str:
    """ATR - Average True Range."""
    return await calculate_indicator(data, 'atr', params)

async def calculate_kc(data: list[dict], params: dict = None) -> str:
    """Keltner Channels."""
    return await calculate_indicator(data, 'kc', params)

async def calculate_donchian(data: list[dict], params: dict = None) -> str:
    """Donchian Channels."""
    return await calculate_indicator(data, 'donchian', params)

async def calculate_accbands(data: list[dict], params: dict = None) -> str:
    """Acceleration Bands."""
    return await calculate_indicator(data, 'accbands', params)

# Volume
async def calculate_obv(data: list[dict], params: dict = None) -> str:
    """OBV - On Balance Volume."""
    return await calculate_indicator(data, 'obv', params)

async def calculate_cmf(data: list[dict], params: dict = None) -> str:
    """CMF - Chaikin Money Flow."""
    return await calculate_indicator(data, 'cmf', params)

async def calculate_mfi(data: list[dict], params: dict = None) -> str:
    """MFI - Money Flow Index."""
    return await calculate_indicator(data, 'mfi', params)

async def calculate_vwap(data: list[dict], params: dict = None) -> str:
    """VWAP - Volume Weighted Average Price."""
    return await calculate_indicator(data, 'vwap', params)

async def calculate_adl(data: list[dict], params: dict = None) -> str:
    """ADL - Accumulation/Distribution Line."""
    return await calculate_indicator(data, 'adl', params)

async def calculate_pvi(data: list[dict], params: dict = None) -> str:
    """PVI - Positive Volume Index."""
    return await calculate_indicator(data, 'pvi', params)

async def calculate_nvi(data: list[dict], params: dict = None) -> str:
    """NVI - Negative Volume Index."""
    return await calculate_indicator(data, 'nvi', params)

