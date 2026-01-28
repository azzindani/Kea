

from mcp_servers.pandas_ta_server.tools.universal import calculate_indicator

# Wrappers

async def calculate_rsi(data: list[dict], params: dict = None) -> str:
    """RSI - Relative Strength Index. Default: length=14."""
    return await calculate_indicator(data, 'rsi', params)

async def calculate_macd(data: list[dict], params: dict = None) -> str:
    """MACD - Moving Average Convergence Divergence."""
    return await calculate_indicator(data, 'macd', params)

async def calculate_stoch(data: list[dict], params: dict = None) -> str:
    """Stochastic Oscillator."""
    return await calculate_indicator(data, 'stoch', params)

async def calculate_cci(data: list[dict], params: dict = None) -> str:
    """CCI - Commodity Channel Index."""
    return await calculate_indicator(data, 'cci', params)

async def calculate_roc(data: list[dict], params: dict = None) -> str:
    """ROC - Rate of Change."""
    return await calculate_indicator(data, 'roc', params)

async def calculate_ao(data: list[dict], params: dict = None) -> str:
    """AO - Awesome Oscillator."""
    return await calculate_indicator(data, 'ao', params)

async def calculate_apo(data: list[dict], params: dict = None) -> str:
    """APO - Absolute Price Oscillator."""
    return await calculate_indicator(data, 'apo', params)

async def calculate_mom(data: list[dict], params: dict = None) -> str:
    """MOM - Momentum."""
    return await calculate_indicator(data, 'mom', params)

async def calculate_tsi(data: list[dict], params: dict = None) -> str:
    """TSI - True Strength Index."""
    return await calculate_indicator(data, 'tsi', params)

async def calculate_uo(data: list[dict], params: dict = None) -> str:
    """UO - Ultimate Oscillator."""
    return await calculate_indicator(data, 'uo', params)

async def calculate_stochrsi(data: list[dict], params: dict = None) -> str:
    """StochRSI - Stochastic RSI."""
    return await calculate_indicator(data, 'stochrsi', params)

async def calculate_squeeze(data: list[dict], params: dict = None) -> str:
    """Squeeze - TTM Squeeze/Momentum."""
    return await calculate_indicator(data, 'squeeze', params)

