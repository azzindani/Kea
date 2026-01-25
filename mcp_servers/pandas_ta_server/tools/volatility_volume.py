
from shared.mcp.protocol import ToolResult
from mcp_servers.pandas_ta_server.tools.universal import calculate_indicator

# Volatility
async def calculate_bbands(arguments: dict) -> ToolResult:
    """Bollinger Bands."""
    arguments['indicator'] = 'bbands'
    return await calculate_indicator(arguments)

async def calculate_atr(arguments: dict) -> ToolResult:
    """ATR - Average True Range."""
    arguments['indicator'] = 'atr'
    return await calculate_indicator(arguments)

async def calculate_kc(arguments: dict) -> ToolResult:
    """Keltner Channels."""
    arguments['indicator'] = 'kc'
    return await calculate_indicator(arguments)

async def calculate_donchian(arguments: dict) -> ToolResult:
    """Donchian Channels."""
    arguments['indicator'] = 'donchian'
    return await calculate_indicator(arguments)

async def calculate_accbands(arguments: dict) -> ToolResult:
    """Acceleration Bands."""
    arguments['indicator'] = 'accbands'
    return await calculate_indicator(arguments)

# Volume
async def calculate_obv(arguments: dict) -> ToolResult:
    """OBV - On Balance Volume."""
    arguments['indicator'] = 'obv'
    return await calculate_indicator(arguments)

async def calculate_cmf(arguments: dict) -> ToolResult:
    """CMF - Chaikin Money Flow."""
    arguments['indicator'] = 'cmf'
    return await calculate_indicator(arguments)

async def calculate_mfi(arguments: dict) -> ToolResult:
    """MFI - Money Flow Index."""
    arguments['indicator'] = 'mfi'
    return await calculate_indicator(arguments)

async def calculate_vwap(arguments: dict) -> ToolResult:
    """VWAP - Volume Weighted Average Price."""
    arguments['indicator'] = 'vwap'
    return await calculate_indicator(arguments)

async def calculate_adl(arguments: dict) -> ToolResult:
    """ADL - Accumulation/Distribution Line."""
    arguments['indicator'] = 'adl'
    return await calculate_indicator(arguments)

async def calculate_pvi(arguments: dict) -> ToolResult:
    """PVI - Positive Volume Index."""
    arguments['indicator'] = 'pvi'
    return await calculate_indicator(arguments)

async def calculate_nvi(arguments: dict) -> ToolResult:
    """NVI - Negative Volume Index."""
    arguments['indicator'] = 'nvi'
    return await calculate_indicator(arguments)
