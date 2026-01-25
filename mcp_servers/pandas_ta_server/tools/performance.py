
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.pandas_ta_server.tools.universal import calculate_indicator

async def calculate_log_return(arguments: dict) -> ToolResult:
    """Calculate Logarithmic Returns."""
    arguments['indicator'] = 'log_return'
    return await calculate_indicator(arguments)

async def calculate_percent_return(arguments: dict) -> ToolResult:
    """Calculate Percentage Returns."""
    arguments['indicator'] = 'percent_return'
    return await calculate_indicator(arguments)

async def calculate_drawdown(arguments: dict) -> ToolResult:
    """Calculate Drawdown."""
    arguments['indicator'] = 'drawdown'
    return await calculate_indicator(arguments)
