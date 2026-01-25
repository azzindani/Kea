
from shared.mcp.protocol import ToolResult
from mcp_servers.finta_server.tools.universal import calculate_indicator

async def calculate_atr(arguments: dict) -> ToolResult:
    """ATR - Average True Range."""
    arguments['indicator'] = 'ATR'
    return await calculate_indicator(arguments)

async def calculate_bbands(arguments: dict) -> ToolResult:
    """BBANDS - Bollinger Bands."""
    arguments['indicator'] = 'BBANDS'
    return await calculate_indicator(arguments)

async def calculate_kc(arguments: dict) -> ToolResult:
    """KC - Keltner Channels."""
    arguments['indicator'] = 'KC'
    return await calculate_indicator(arguments)

async def calculate_do(arguments: dict) -> ToolResult:
    """DO - Donchian Channels."""
    arguments['indicator'] = 'DO'
    return await calculate_indicator(arguments)

async def calculate_mobo(arguments: dict) -> ToolResult:
    """MOBO - Momentum Breakout Bands."""
    arguments['indicator'] = 'MOBO'
    return await calculate_indicator(arguments)

async def calculate_tr(arguments: dict) -> ToolResult:
    """TR - True Range."""
    arguments['indicator'] = 'TR'
    return await calculate_indicator(arguments)

async def calculate_bbwidth(arguments: dict) -> ToolResult:
    """BBWIDTH - Bollinger Band Width."""
    arguments['indicator'] = 'BBWIDTH'
    return await calculate_indicator(arguments)

async def calculate_percent_b(arguments: dict) -> ToolResult:
    """PERCENT_B - Percent B."""
    arguments['indicator'] = 'PERCENT_B'
    return await calculate_indicator(arguments)

async def calculate_apz(arguments: dict) -> ToolResult:
    """APZ - Adaptive Price Zone."""
    arguments['indicator'] = 'APZ'
    return await calculate_indicator(arguments)

async def calculate_massi(arguments: dict) -> ToolResult:
    """MASSI - Mass Index."""
    arguments['indicator'] = 'MASSI'
    return await calculate_indicator(arguments)
