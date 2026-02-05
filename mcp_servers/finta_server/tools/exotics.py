

from mcp_servers.finta_server.tools.universal import calculate_indicator


async def calculate_wto(data: list[dict], params: dict = None) -> str:
    """WTO - Wave Trend Oscillator."""
    return await calculate_indicator(data, 'WTO', params)

async def calculate_stc(data: list[dict], params: dict = None) -> str:
    """STC - Schaff Trend Cycle."""
    return await calculate_indicator(data, 'STC', params)

async def calculate_ev_macd(data: list[dict], params: dict = None) -> str:
    """EV_MACD - Elastic Volume MACD."""
    return await calculate_indicator(data, 'EV_MACD', params)

async def calculate_alma(data: list[dict], params: dict = None) -> str:
    """ALMA - Arnaud Legoux Moving Average."""
    return await calculate_indicator(data, 'ALMA', params)

async def calculate_vama(data: list[dict], params: dict = None) -> str:
    """VAMA - Volume Adjusted Moving Average."""
    return await calculate_indicator(data, 'VAMA', params)

async def calculate_kaufman(data: list[dict], params: dict = None) -> str:
    """ER - Kaufman Efficiency Ratio."""
    return await calculate_indicator(data, 'ER', params)

