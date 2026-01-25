
from shared.mcp.protocol import ToolResult
from mcp_servers.finta_server.tools.universal import calculate_indicator

async def calculate_vfi(arguments: dict) -> ToolResult:
    """VFI - Volume Flow Indicator."""
    arguments['indicator'] = 'VFI'
    return await calculate_indicator(arguments)

async def calculate_fve(arguments: dict) -> ToolResult:
    """FVE - Finite Volume Element."""
    arguments['indicator'] = 'FVE'
    return await calculate_indicator(arguments)

async def calculate_qstick(arguments: dict) -> ToolResult:
    """QSTICK - Chande's QStick."""
    arguments['indicator'] = 'QSTICK'
    return await calculate_indicator(arguments)

async def calculate_msd(arguments: dict) -> ToolResult:
    """MSD - Moving Standard Deviation."""
    arguments['indicator'] = 'MSD'
    return await calculate_indicator(arguments)
