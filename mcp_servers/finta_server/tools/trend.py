
from shared.mcp.protocol import ToolResult
from mcp_servers.finta_server.tools.universal import calculate_indicator

async def calculate_sma(arguments: dict) -> ToolResult:
    """SMA - Simple Moving Average."""
    arguments['indicator'] = 'SMA'
    return await calculate_indicator(arguments)

async def calculate_ema(arguments: dict) -> ToolResult:
    """EMA - Exponential Moving Average."""
    arguments['indicator'] = 'EMA'
    return await calculate_indicator(arguments)

async def calculate_dema(arguments: dict) -> ToolResult:
    """DEMA - Double Exponential Moving Average."""
    arguments['indicator'] = 'DEMA'
    return await calculate_indicator(arguments)

async def calculate_tema(arguments: dict) -> ToolResult:
    """TEMA - Triple Exponential Moving Average."""
    arguments['indicator'] = 'TEMA'
    return await calculate_indicator(arguments)

async def calculate_trima(arguments: dict) -> ToolResult:
    """TRIMA - Triangular Moving Average."""
    arguments['indicator'] = 'TRIMA'
    return await calculate_indicator(arguments)

async def calculate_wma(arguments: dict) -> ToolResult:
    """WMA - Weighted Moving Average."""
    arguments['indicator'] = 'WMA'
    return await calculate_indicator(arguments)

async def calculate_hma(arguments: dict) -> ToolResult:
    """HMA - Hull Moving Average."""
    arguments['indicator'] = 'HMA'
    return await calculate_indicator(arguments)

async def calculate_zlema(arguments: dict) -> ToolResult:
    """ZLEMA - Zero Lag EMA."""
    arguments['indicator'] = 'ZLEMA'
    return await calculate_indicator(arguments)

async def calculate_adx(arguments: dict) -> ToolResult:
    """ADX - Average Directional Index."""
    arguments['indicator'] = 'ADX'
    return await calculate_indicator(arguments)

async def calculate_ssma(arguments: dict) -> ToolResult:
    """SSMA - Smoothed SMA."""
    arguments['indicator'] = 'SSMA'
    return await calculate_indicator(arguments)

async def calculate_smma(arguments: dict) -> ToolResult:
    """SMMA - Smoothed Moving Average."""
    arguments['indicator'] = 'SMMA'
    return await calculate_indicator(arguments)

async def calculate_frama(arguments: dict) -> ToolResult:
    """FRAMA - Fractal Adaptive Moving Average."""
    arguments['indicator'] = 'FRAMA'
    return await calculate_indicator(arguments)

async def calculate_sar(arguments: dict) -> ToolResult:
    """SAR - Stop and Reverse."""
    arguments['indicator'] = 'SAR'
    return await calculate_indicator(arguments)
