

from mcp_servers.finta_server.tools.universal import calculate_indicator


async def calculate_chandelier(data: list[dict], params: dict = None) -> str:
    """CHANDELIER - Chandelier Exit."""
    return await calculate_indicator(data, 'CHANDELIER', params)

