
from shared.mcp.protocol import ToolResult
from mcp_servers.finta_server.tools.universal import calculate_indicator

async def calculate_vwap(arguments: dict) -> ToolResult:
    """VWAP - Volume Weighted Average Price."""
    arguments['indicator'] = 'VWAP'
    return await calculate_indicator(arguments)

async def calculate_evwma(arguments: dict) -> ToolResult:
    """EVWMA - Elastic Volume Weighted Moving Average."""
    arguments['indicator'] = 'EVWMA'
    return await calculate_indicator(arguments)

async def calculate_wobv(arguments: dict) -> ToolResult:
    """WOBV - Weighted On Balance Volume."""
    arguments['indicator'] = 'WOBV'
    return await calculate_indicator(arguments)
