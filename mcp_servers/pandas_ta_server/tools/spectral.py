

from mcp_servers.pandas_ta_server.tools.universal import calculate_indicator


async def calculate_fisher(data: list[dict], params: dict = None) -> str:
    """Calculates Fisher Transform."""
    return await calculate_indicator(data, 'fisher', params)

async def calculate_cg(data: list[dict], params: dict = None) -> str:
    """Calculates Center of Gravity."""
    return await calculate_indicator(data, 'cg', params)

