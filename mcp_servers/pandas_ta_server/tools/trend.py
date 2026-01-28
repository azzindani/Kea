

from mcp_servers.pandas_ta_server.tools.universal import calculate_indicator


async def calculate_sma(data: list[dict], params: dict = None) -> str:
    """SMA - Simple Moving Average."""
    return await calculate_indicator(data, 'sma', params)

async def calculate_ema(data: list[dict], params: dict = None) -> str:
    """EMA - Exponential Moving Average."""
    return await calculate_indicator(data, 'ema', params)

async def calculate_wma(data: list[dict], params: dict = None) -> str:
    """WMA - Weighted Moving Average."""
    return await calculate_indicator(data, 'wma', params)

async def calculate_hma(data: list[dict], params: dict = None) -> str:
    """HMA - Hull Moving Average."""
    return await calculate_indicator(data, 'hma', params)

async def calculate_adx(data: list[dict], params: dict = None) -> str:
    """ADX - Average Directional Index."""
    return await calculate_indicator(data, 'adx', params)

async def calculate_supertrend(data: list[dict], params: dict = None) -> str:
    """Supertrend."""
    return await calculate_indicator(data, 'supertrend', params)

async def calculate_vortex(data: list[dict], params: dict = None) -> str:
    """Vortex Oscillator."""
    return await calculate_indicator(data, 'vortex', params)

async def calculate_aroon(data: list[dict], params: dict = None) -> str:
    """Aroon Indicator."""
    return await calculate_indicator(data, 'aroon', params)

async def calculate_dpo(data: list[dict], params: dict = None) -> str:
    """DPO - Detrended Price Oscillator."""
    return await calculate_indicator(data, 'dpo', params)

async def calculate_psar(data: list[dict], params: dict = None) -> str:
    """PSAR - Parabolic SAR."""
    return await calculate_indicator(data, 'psar', params)

async def calculate_ichimoku(data: list[dict], params: dict = None) -> str:
    """Ichimoku Kinko Hyo (Cloud)."""
    return await calculate_indicator(data, 'ichimoku', params)

