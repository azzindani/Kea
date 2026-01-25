
from shared.mcp.protocol import ToolResult
from mcp_servers.finta_server.tools.universal import calculate_indicator

async def calculate_ichimoku(arguments: dict) -> ToolResult:
    """ICHIMOKU - Ichimoku Cloud."""
    arguments['indicator'] = 'ICHIMOKU'
    return await calculate_indicator(arguments)
