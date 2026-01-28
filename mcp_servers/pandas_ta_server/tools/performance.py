

from mcp_servers.pandas_ta_server.tools.universal import calculate_indicator


async def calculate_log_return(data: list[dict], params: dict = None) -> str:
    """Calculate Logarithmic Returns."""
    return await calculate_indicator(data, 'log_return', params)

async def calculate_percent_return(data: list[dict], params: dict = None) -> str:
    """Calculate Percentage Returns."""
    return await calculate_indicator(data, 'percent_return', params)

async def calculate_drawdown(data: list[dict], params: dict = None) -> str:
    """Calculate Drawdown."""
    return await calculate_indicator(data, 'drawdown', params)

