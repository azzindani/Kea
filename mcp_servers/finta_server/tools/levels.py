

from mcp_servers.finta_server.tools.universal import calculate_indicator


async def calculate_pivot(data: list[dict], params: dict = None) -> str:
    """PIVOT - Standard Pivot Points."""
    return await calculate_indicator(data, 'PIVOT', params)

async def calculate_fib_pivot(data: list[dict], params: dict = None) -> str:
    """PIVOT_FIB - Fibonacci Pivot Points."""
    return await calculate_indicator(data, 'PIVOT_FIB', params)

