
from shared.mcp.protocol import ToolResult
from mcp_servers.finta_server.tools.universal import calculate_indicator

async def calculate_obv(arguments: dict) -> ToolResult:
    """OBV - On Balance Volume."""
    arguments['indicator'] = 'OBV'
    return await calculate_indicator(arguments)

async def calculate_mfi(arguments: dict) -> ToolResult:
    """MFI - Money Flow Index."""
    arguments['indicator'] = 'MFI'
    return await calculate_indicator(arguments)

async def calculate_adl(arguments: dict) -> ToolResult:
    """ADL - Accumulation/Distribution Line."""
    arguments['indicator'] = 'ADL'
    return await calculate_indicator(arguments)

async def calculate_chaikin(arguments: dict) -> ToolResult:
    """CHAIKIN - Chaikin Oscillator."""
    arguments['indicator'] = 'CHAIKIN'
    return await calculate_indicator(arguments)

async def calculate_efi(arguments: dict) -> ToolResult:
    """EFI - Elder's Force Index."""
    arguments['indicator'] = 'EFI'
    return await calculate_indicator(arguments)

async def calculate_vpt(arguments: dict) -> ToolResult:
    """VPT - Volume Price Trend."""
    arguments['indicator'] = 'VPT'
    return await calculate_indicator(arguments)

async def calculate_emv(arguments: dict) -> ToolResult:
    """EMV - Ease of Movement."""
    arguments['indicator'] = 'EMV'
    return await calculate_indicator(arguments)

async def calculate_nvi(arguments: dict) -> ToolResult:
    """NVI - Negative Volume Index."""
    arguments['indicator'] = 'NVI'
    return await calculate_indicator(arguments)

async def calculate_pvi(arguments: dict) -> ToolResult:
    """PVI - Positive Volume Index."""
    arguments['indicator'] = 'PVI'
    return await calculate_indicator(arguments)

async def calculate_vzo(arguments: dict) -> ToolResult:
    """VZO - Volume Zone Oscillator."""
    arguments['indicator'] = 'VZO'
    return await calculate_indicator(arguments)
