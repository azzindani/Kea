

from mcp_servers.finta_server.tools.universal import calculate_indicator


async def calculate_ichimoku(data: list[dict], params: dict = None) -> str:
    """ICHIMOKU - Ichimoku Cloud."""
    return await calculate_indicator(data, 'ICHIMOKU', params)

