
from shared.mcp.protocol import ToolResult
from mcp_servers.finta_server.tools.universal import calculate_indicator

async def calculate_basp(arguments: dict) -> ToolResult:
    """BASP - Buy and Sell Pressure."""
    arguments['indicator'] = 'BASP'
    return await calculate_indicator(arguments)

async def calculate_baspn(arguments: dict) -> ToolResult:
    """BASPN - Normalized BASP."""
    arguments['indicator'] = 'BASPN'
    return await calculate_indicator(arguments)

async def calculate_ebbp(arguments: dict) -> ToolResult:
    """EBBP - Bull Power and Bear Power."""
    arguments['indicator'] = 'EBBP'
    return await calculate_indicator(arguments)

async def calculate_uo(arguments: dict) -> ToolResult:
    """UO - Ultimate Oscillator (Pressure)."""
    arguments['indicator'] = 'UO'
    return await calculate_indicator(arguments)
