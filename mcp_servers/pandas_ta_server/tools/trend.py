
from shared.mcp.protocol import ToolResult
from mcp_servers.pandas_ta_server.tools.universal import calculate_indicator

async def calculate_sma(arguments: dict) -> ToolResult:
    """SMA - Simple Moving Average."""
    arguments['indicator'] = 'sma'
    return await calculate_indicator(arguments)

async def calculate_ema(arguments: dict) -> ToolResult:
    """EMA - Exponential Moving Average."""
    arguments['indicator'] = 'ema'
    return await calculate_indicator(arguments)

async def calculate_wma(arguments: dict) -> ToolResult:
    """WMA - Weighted Moving Average."""
    arguments['indicator'] = 'wma'
    return await calculate_indicator(arguments)

async def calculate_hma(arguments: dict) -> ToolResult:
    """HMA - Hull Moving Average."""
    arguments['indicator'] = 'hma'
    return await calculate_indicator(arguments)

async def calculate_adx(arguments: dict) -> ToolResult:
    """ADX - Average Directional Index."""
    arguments['indicator'] = 'adx'
    return await calculate_indicator(arguments)

async def calculate_supertrend(arguments: dict) -> ToolResult:
    """Supertrend."""
    arguments['indicator'] = 'supertrend'
    return await calculate_indicator(arguments)

async def calculate_vortex(arguments: dict) -> ToolResult:
    """Vortex Oscillator."""
    arguments['indicator'] = 'vortex'
    return await calculate_indicator(arguments)

async def calculate_aroon(arguments: dict) -> ToolResult:
    """Aroon Indicator."""
    arguments['indicator'] = 'aroon'
    return await calculate_indicator(arguments)

async def calculate_dpo(arguments: dict) -> ToolResult:
    """DPO - Detrended Price Oscillator."""
    arguments['indicator'] = 'dpo'
    return await calculate_indicator(arguments)

async def calculate_psar(arguments: dict) -> ToolResult:
    """PSAR - Parabolic SAR."""
    arguments['indicator'] = 'psar'
    return await calculate_indicator(arguments)

async def calculate_ichimoku(arguments: dict) -> ToolResult:
    """Ichimoku Kinko Hyo (Cloud)."""
    arguments['indicator'] = 'ichimoku'
    return await calculate_indicator(arguments)
