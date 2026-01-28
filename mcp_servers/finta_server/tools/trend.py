

from mcp_servers.finta_server.tools.universal import calculate_indicator


async def calculate_sma(data: list[dict], params: dict = None) -> str:
    """SMA - Simple Moving Average."""
    return await calculate_indicator(data, 'SMA', params)

async def calculate_ema(data: list[dict], params: dict = None) -> str:
    """EMA - Exponential Moving Average."""
    return await calculate_indicator(data, 'EMA', params)

async def calculate_dema(data: list[dict], params: dict = None) -> str:
    """DEMA - Double Exponential Moving Average."""
    return await calculate_indicator(data, 'DEMA', params)

async def calculate_tema(data: list[dict], params: dict = None) -> str:
    """TEMA - Triple Exponential Moving Average."""
    return await calculate_indicator(data, 'TEMA', params)

async def calculate_trima(data: list[dict], params: dict = None) -> str:
    """TRIMA - Triangular Moving Average."""
    return await calculate_indicator(data, 'TRIMA', params)

async def calculate_wma(data: list[dict], params: dict = None) -> str:
    """WMA - Weighted Moving Average."""
    return await calculate_indicator(data, 'WMA', params)

async def calculate_hma(data: list[dict], params: dict = None) -> str:
    """HMA - Hull Moving Average."""
    return await calculate_indicator(data, 'HMA', params)

async def calculate_zlema(data: list[dict], params: dict = None) -> str:
    """ZLEMA - Zero Lag EMA."""
    return await calculate_indicator(data, 'ZLEMA', params)

async def calculate_adx(data: list[dict], params: dict = None) -> str:
    """ADX - Average Directional Index."""
    return await calculate_indicator(data, 'ADX', params)

async def calculate_ssma(data: list[dict], params: dict = None) -> str:
    """SSMA - Smoothed SMA."""
    return await calculate_indicator(data, 'SSMA', params)

async def calculate_smma(data: list[dict], params: dict = None) -> str:
    """SMMA - Smoothed Moving Average."""
    return await calculate_indicator(data, 'SMMA', params)

async def calculate_frama(data: list[dict], params: dict = None) -> str:
    """FRAMA - Fractal Adaptive Moving Average."""
    return await calculate_indicator(data, 'FRAMA', params)

async def calculate_sar(data: list[dict], params: dict = None) -> str:
    """SAR - Stop and Reverse."""
    return await calculate_indicator(data, 'SAR', params)

