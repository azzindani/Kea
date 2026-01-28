

from mcp_servers.finta_server.tools.universal import calculate_indicator


async def calculate_rsi(data: list[dict], params: dict = None) -> str:
    """RSI - Relative Strength Index."""
    return await calculate_indicator(data, 'RSI', params)

async def calculate_macd(data: list[dict], params: dict = None) -> str:
    """MACD - Moving Average Convergence Divergence."""
    return await calculate_indicator(data, 'MACD', params)

async def calculate_stoch(data: list[dict], params: dict = None) -> str:
    """STOCH - Stochastic Oscillator."""
    return await calculate_indicator(data, 'STOCH', params)

async def calculate_tsi(data: list[dict], params: dict = None) -> str:
    """TSI - True Strength Index."""
    return await calculate_indicator(data, 'TSI', params)

async def calculate_uo(data: list[dict], params: dict = None) -> str:
    """UO - Ultimate Oscillator."""
    return await calculate_indicator(data, 'UO', params)

async def calculate_roc(data: list[dict], params: dict = None) -> str:
    """ROC - Rate of Change."""
    return await calculate_indicator(data, 'ROC', params)

async def calculate_mom(data: list[dict], params: dict = None) -> str:
    """MOM - Momentum."""
    return await calculate_indicator(data, 'MOM', params)

async def calculate_ao(data: list[dict], params: dict = None) -> str:
    """AO - Awesome Oscillator."""
    return await calculate_indicator(data, 'AO', params)

async def calculate_williams(data: list[dict], params: dict = None) -> str:
    """WILLIAMS - Williams %R."""
    return await calculate_indicator(data, 'WILLIAMS', params)

async def calculate_cmo(data: list[dict], params: dict = None) -> str:
    """CMO - Chande Momentum Oscillator."""
    return await calculate_indicator(data, 'CMO', params)

async def calculate_coppock(data: list[dict], params: dict = None) -> str:
    """COPP - Coppock Curve."""
    return await calculate_indicator(data, 'COPP', params)

async def calculate_fish(data: list[dict], params: dict = None) -> str:
    """FISH - Fisher Transform."""
    return await calculate_indicator(data, 'FISH', params)

async def calculate_kama(data: list[dict], params: dict = None) -> str:
    """KAMA - Kaufman's Adaptive Moving Average."""
    return await calculate_indicator(data, 'KAMA', params)

async def calculate_vortex(data: list[dict], params: dict = None) -> str:
    """VORTEX - Vortex Indicator."""
    return await calculate_indicator(data, 'VORTEX', params)

async def calculate_kst(data: list[dict], params: dict = None) -> str:
    """KST - Know Sure Thing."""
    return await calculate_indicator(data, 'KST', params)

