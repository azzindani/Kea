

from mcp_servers.finta_server.tools.universal import calculate_indicator


async def calculate_basp(data: list[dict], params: dict = None) -> str:
    """BASP - Buy and Sell Pressure."""
    return await calculate_indicator(data, 'BASP', params)

async def calculate_baspn(data: list[dict], params: dict = None) -> str:
    """BASPN - Normalized BASP."""
    return await calculate_indicator(data, 'BASPN', params)

async def calculate_ebbp(data: list[dict], params: dict = None) -> str:
    """EBBP - Bull Power and Bear Power."""
    return await calculate_indicator(data, 'EBBP', params)

async def calculate_uo_pressure(data: list[dict], params: dict = None) -> str:
    """UO - Ultimate Oscillator (Pressure)."""
    # Renamed to avoid specific conflict if imported together, though tools are isolated.
    return await calculate_indicator(data, 'UO', params)

