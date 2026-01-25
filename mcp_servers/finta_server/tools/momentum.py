
from shared.mcp.protocol import ToolResult
from mcp_servers.finta_server.tools.universal import calculate_indicator

async def calculate_rsi(arguments: dict) -> ToolResult:
    """RSI - Relative Strength Index."""
    arguments['indicator'] = 'RSI'
    return await calculate_indicator(arguments)

async def calculate_macd(arguments: dict) -> ToolResult:
    """MACD - Moving Average Convergence Divergence."""
    arguments['indicator'] = 'MACD'
    return await calculate_indicator(arguments)

async def calculate_stoch(arguments: dict) -> ToolResult:
    """STOCH - Stochastic Oscillator."""
    arguments['indicator'] = 'STOCH'
    return await calculate_indicator(arguments)

async def calculate_tsi(arguments: dict) -> ToolResult:
    """TSI - True Strength Index."""
    arguments['indicator'] = 'TSI'
    return await calculate_indicator(arguments)

async def calculate_uo(arguments: dict) -> ToolResult:
    """UO - Ultimate Oscillator."""
    arguments['indicator'] = 'UO'
    return await calculate_indicator(arguments)

async def calculate_roc(arguments: dict) -> ToolResult:
    """ROC - Rate of Change."""
    arguments['indicator'] = 'ROC'
    return await calculate_indicator(arguments)

async def calculate_mom(arguments: dict) -> ToolResult:
    """MOM - Momentum."""
    arguments['indicator'] = 'MOM'
    return await calculate_indicator(arguments)

async def calculate_ao(arguments: dict) -> ToolResult:
    """AO - Awesome Oscillator."""
    arguments['indicator'] = 'AO'
    return await calculate_indicator(arguments)

async def calculate_williams(arguments: dict) -> ToolResult:
    """WILLIAMS - Williams %R."""
    arguments['indicator'] = 'WILLIAMS'
    return await calculate_indicator(arguments)

async def calculate_cmo(arguments: dict) -> ToolResult:
    """CMO - Chande Momentum Oscillator."""
    arguments['indicator'] = 'CMO'
    return await calculate_indicator(arguments)

async def calculate_coppock(arguments: dict) -> ToolResult:
    """COPP - Coppock Curve."""
    arguments['indicator'] = 'COPP'
    return await calculate_indicator(arguments)

async def calculate_fish(arguments: dict) -> ToolResult:
    """FISH - Fisher Transform."""
    arguments['indicator'] = 'FISH'
    return await calculate_indicator(arguments)

async def calculate_kama(arguments: dict) -> ToolResult:
    """KAMA - Kaufman's Adaptive Moving Average."""
    arguments['indicator'] = 'KAMA'
    return await calculate_indicator(arguments)

async def calculate_vortex(arguments: dict) -> ToolResult:
    """VORTEX - Vortex Indicator."""
    arguments['indicator'] = 'VORTEX'
    return await calculate_indicator(arguments)

async def calculate_kst(arguments: dict) -> ToolResult:
    """KST - Know Sure Thing."""
    arguments['indicator'] = 'KST'
    return await calculate_indicator(arguments)
