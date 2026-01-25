
from shared.mcp.protocol import ToolResult
from mcp_servers.finta_server.tools.universal import calculate_indicator

async def calculate_chandelier(arguments: dict) -> ToolResult:
    """CHANDELIER - Chandelier Exit."""
    arguments['indicator'] = 'CHANDELIER'
    return await calculate_indicator(arguments)
