
from shared.mcp.protocol import ToolResult
from mcp_servers.pandas_ta_server.tools.universal import calculate_indicator

async def calculate_fisher(arguments: dict) -> ToolResult:
    """Calculates Fisher Transform."""
    arguments['indicator'] = 'fisher'
    return await calculate_indicator(arguments)

async def calculate_cg(arguments: dict) -> ToolResult:
    """Calculates Center of Gravity."""
    arguments['indicator'] = 'cg'
    return await calculate_indicator(arguments)
