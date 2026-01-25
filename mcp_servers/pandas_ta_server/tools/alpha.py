
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.pandas_ta_server.tools.universal import calculate_indicator

async def calculate_rsx(arguments: dict) -> ToolResult:
    """Calculates Relative Strength Xtra (Jurik RSI). Smoother."""
    arguments['indicator'] = 'rsx'
    return await calculate_indicator(arguments)

async def calculate_thermo(arguments: dict) -> ToolResult:
    """Calculates Elder's Thermometer (Volatility)."""
    arguments['indicator'] = 'thermo'
    return await calculate_indicator(arguments)

async def calculate_massi(arguments: dict) -> ToolResult:
    """Calculates Mass Index (Reversal)."""
    arguments['indicator'] = 'massi'
    return await calculate_indicator(arguments)

async def calculate_ui(arguments: dict) -> ToolResult:
    """Calculates Ulcer Index (Downside Risk)."""
    arguments['indicator'] = 'ui'
    return await calculate_indicator(arguments)

async def calculate_natr(arguments: dict) -> ToolResult:
    """Calculates Normalized ATR."""
    arguments['indicator'] = 'natr'
    return await calculate_indicator(arguments)
