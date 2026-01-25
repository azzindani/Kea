
from shared.mcp.protocol import ToolResult
from mcp_servers.finta_server.tools.universal import calculate_indicator

async def calculate_pivot(arguments: dict) -> ToolResult:
    """PIVOT - Standard Pivot Points."""
    arguments['indicator'] = 'PIVOT'
    return await calculate_indicator(arguments)

async def calculate_fib_pivot(arguments: dict) -> ToolResult:
    """PIVOT_FIB - Fibonacci Pivot Points."""
    arguments['indicator'] = 'PIVOT_FIB'
    return await calculate_indicator(arguments)
