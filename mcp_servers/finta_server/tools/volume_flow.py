

from mcp_servers.finta_server.tools.universal import calculate_indicator


async def calculate_vfi(data: list[dict], params: dict = None) -> str:
    """VFI - Volume Flow Indicator."""
    return await calculate_indicator(data, 'VFI', params)

async def calculate_fve(data: list[dict], params: dict = None) -> str:
    """FVE - Finite Volume Element."""
    return await calculate_indicator(data, 'FVE', params)

async def calculate_qstick(data: list[dict], params: dict = None) -> str:
    """QSTICK - Chande's QStick."""
    return await calculate_indicator(data, 'QSTICK', params)

async def calculate_msd(data: list[dict], params: dict = None) -> str:
    """MSD - Moving Standard Deviation."""
    return await calculate_indicator(data, 'MSD', params)

