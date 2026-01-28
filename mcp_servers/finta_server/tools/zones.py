

from mcp_servers.finta_server.tools.universal import calculate_indicator


async def calculate_pzo(data: list[dict], params: dict = None) -> str:
    """PZO - Price Zone Oscillator."""
    return await calculate_indicator(data, 'PZO', params)

async def calculate_cfi(data: list[dict], params: dict = None) -> str:
    """CFI - Cumulative Force Index."""
    return await calculate_indicator(data, 'CFI', params)

async def calculate_tp(data: list[dict], params: dict = None) -> str:
    """TP - Typical Price."""
    return await calculate_indicator(data, 'TP', params)

