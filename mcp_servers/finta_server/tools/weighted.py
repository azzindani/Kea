

from mcp_servers.finta_server.tools.universal import calculate_indicator


async def calculate_vwap(data: list[dict], params: dict = None) -> str:
    """VWAP - Volume Weighted Average Price."""
    return await calculate_indicator(data, 'VWAP', params)

async def calculate_evwma(data: list[dict], params: dict = None) -> str:
    """EVWMA - Elastic Volume Weighted Moving Average."""
    return await calculate_indicator(data, 'EVWMA', params)

async def calculate_wobv(data: list[dict], params: dict = None) -> str:
    """WOBV - Weighted On Balance Volume."""
    return await calculate_indicator(data, 'WOBV', params)

