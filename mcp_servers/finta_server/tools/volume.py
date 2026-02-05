

from mcp_servers.finta_server.tools.universal import calculate_indicator


async def calculate_obv(data: list[dict], params: dict = None) -> str:
    """OBV - On Balance Volume."""
    return await calculate_indicator(data, 'OBV', params)

async def calculate_mfi(data: list[dict], params: dict = None) -> str:
    """MFI - Money Flow Index."""
    return await calculate_indicator(data, 'MFI', params)

async def calculate_adl(data: list[dict], params: dict = None) -> str:
    """ADL - Accumulation/Distribution Line."""
    return await calculate_indicator(data, 'ADL', params)

async def calculate_chaikin(data: list[dict], params: dict = None) -> str:
    """CHAIKIN - Chaikin Oscillator."""
    return await calculate_indicator(data, 'CHAIKIN', params)

async def calculate_efi(data: list[dict], params: dict = None) -> str:
    """EFI - Elder's Force Index."""
    return await calculate_indicator(data, 'EFI', params)

async def calculate_vpt(data: list[dict], params: dict = None) -> str:
    """VPT - Volume Price Trend."""
    return await calculate_indicator(data, 'VPT', params)

async def calculate_emv(data: list[dict], params: dict = None) -> str:
    """EMV - Ease of Movement."""
    return await calculate_indicator(data, 'EMV', params)

async def calculate_nvi(data: list[dict], params: dict = None) -> str:
    """NVI - Negative Volume Index."""
    return await calculate_indicator(data, 'NVI', params)

async def calculate_pvi(data: list[dict], params: dict = None) -> str:
    """PVI - Positive Volume Index."""
    return await calculate_indicator(data, 'PVI', params)

async def calculate_vzo(data: list[dict], params: dict = None) -> str:
    """VZO - Volume Zone Oscillator."""
    return await calculate_indicator(data, 'VZO', params)

