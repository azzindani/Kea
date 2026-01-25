
from shared.mcp.protocol import ToolResult
from mcp_servers.finta_server.tools.universal import calculate_indicator

async def calculate_wto(arguments: dict) -> ToolResult:
    """WTO - Wave Trend Oscillator."""
    arguments['indicator'] = 'WTO'
    return await calculate_indicator(arguments)

async def calculate_stc(arguments: dict) -> ToolResult:
    """STC - Schaff Trend Cycle."""
    arguments['indicator'] = 'STC'
    return await calculate_indicator(arguments)

async def calculate_ev_macd(arguments: dict) -> ToolResult:
    """EV_MACD - Elastic Volume MACD."""
    arguments['indicator'] = 'EV_MACD'
    return await calculate_indicator(arguments)

async def calculate_alma(arguments: dict) -> ToolResult:
    """ALMA - Arnaud Legoux Moving Average."""
    arguments['indicator'] = 'ALMA'
    return await calculate_indicator(arguments)

async def calculate_vama(arguments: dict) -> ToolResult:
    """VAMA - Volume Adjusted Moving Average."""
    arguments['indicator'] = 'VAMA'
    return await calculate_indicator(arguments)

async def calculate_kaufman(arguments: dict) -> ToolResult:
    """ER - Kaufman Efficiency Ratio."""
    arguments['indicator'] = 'ER'
    return await calculate_indicator(arguments)
