
from shared.mcp.protocol import ToolResult
from mcp_servers.pandas_ta_server.tools.universal import calculate_indicator

# Wrappers
async def calculate_rsi(arguments: dict) -> ToolResult:
    """RSI - Relative Strength Index. Default: length=14."""
    arguments['indicator'] = 'rsi'
    return await calculate_indicator(arguments)

async def calculate_macd(arguments: dict) -> ToolResult:
    """MACD - Moving Average Convergence Divergence."""
    arguments['indicator'] = 'macd'
    return await calculate_indicator(arguments)

async def calculate_stoch(arguments: dict) -> ToolResult:
    """Stochastic Oscillator."""
    arguments['indicator'] = 'stoch'
    return await calculate_indicator(arguments)

async def calculate_cci(arguments: dict) -> ToolResult:
    """CCI - Commodity Channel Index."""
    arguments['indicator'] = 'cci'
    return await calculate_indicator(arguments)

async def calculate_roc(arguments: dict) -> ToolResult:
    """ROC - Rate of Change."""
    arguments['indicator'] = 'roc'
    return await calculate_indicator(arguments)

async def calculate_ao(arguments: dict) -> ToolResult:
    """AO - Awesome Oscillator."""
    arguments['indicator'] = 'ao'
    return await calculate_indicator(arguments)

async def calculate_apo(arguments: dict) -> ToolResult:
    """APO - Absolute Price Oscillator."""
    arguments['indicator'] = 'apo'
    return await calculate_indicator(arguments)

async def calculate_mom(arguments: dict) -> ToolResult:
    """MOM - Momentum."""
    arguments['indicator'] = 'mom'
    return await calculate_indicator(arguments)

async def calculate_tsi(arguments: dict) -> ToolResult:
    """TSI - True Strength Index."""
    arguments['indicator'] = 'tsi'
    return await calculate_indicator(arguments)

async def calculate_uo(arguments: dict) -> ToolResult:
    """UO - Ultimate Oscillator."""
    arguments['indicator'] = 'uo'
    return await calculate_indicator(arguments)

async def calculate_stochrsi(arguments: dict) -> ToolResult:
    """StochRSI - Stochastic RSI."""
    arguments['indicator'] = 'stochrsi'
    return await calculate_indicator(arguments)

async def calculate_squeeze(arguments: dict) -> ToolResult:
    """Squeeze - TTM Squeeze/Momentum."""
    arguments['indicator'] = 'squeeze'
    return await calculate_indicator(arguments)
