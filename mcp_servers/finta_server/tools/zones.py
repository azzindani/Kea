
from shared.mcp.protocol import ToolResult
from mcp_servers.finta_server.tools.universal import calculate_indicator

async def calculate_pzo(arguments: dict) -> ToolResult:
    """PZO - Price Zone Oscillator."""
    arguments['indicator'] = 'PZO'
    return await calculate_indicator(arguments)

async def calculate_cfi(arguments: dict) -> ToolResult:
    """CFI - Cumulative Force Index."""
    arguments['indicator'] = 'CFI'
    return await calculate_indicator(arguments)

async def calculate_tp(arguments: dict) -> ToolResult:
    """TP - Typical Price."""
    arguments['indicator'] = 'TP'
    return await calculate_indicator(arguments)
