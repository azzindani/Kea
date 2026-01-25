
from shared.mcp.protocol import ToolResult
from mcp_servers.pandas_ta_server.tools.universal import calculate_indicator

# Wrappers for common candle patterns
async def calculate_cdl_doji(arguments: dict) -> ToolResult:
    """Candle: Doji."""
    arguments['indicator'] = 'cdl_doji'
    return await calculate_indicator(arguments)

async def calculate_cdl_hammer(arguments: dict) -> ToolResult:
    """Candle: Hammer."""
    arguments['indicator'] = 'cdl_hammer'
    return await calculate_indicator(arguments)

async def calculate_cdl_engulfing(arguments: dict) -> ToolResult:
    """Candle: Engulfing."""
    arguments['indicator'] = 'cdl_engulfing'
    return await calculate_indicator(arguments)

async def calculate_cdl_morningstar(arguments: dict) -> ToolResult:
    """Candle: Morning Star."""
    arguments['indicator'] = 'cdl_morningstar'
    return await calculate_indicator(arguments)

async def calculate_cdl_eveningstar(arguments: dict) -> ToolResult:
    """Candle: Evening Star."""
    arguments['indicator'] = 'cdl_eveningstar'
    return await calculate_indicator(arguments)
