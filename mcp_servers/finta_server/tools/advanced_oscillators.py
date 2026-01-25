
from shared.mcp.protocol import ToolResult
from mcp_servers.finta_server.tools.universal import calculate_indicator

async def calculate_trix(arguments: dict) -> ToolResult:
    """TRIX - Triple Exponential Average Oscillator."""
    arguments['indicator'] = 'TRIX'
    return await calculate_indicator(arguments)

async def calculate_ift_rsi(arguments: dict) -> ToolResult:
    """IFT_RSI - Inverse Fisher Transform RSI."""
    arguments['indicator'] = 'IFT_RSI'
    return await calculate_indicator(arguments)

async def calculate_sqzmi(arguments: dict) -> ToolResult:
    """SQZMI - Squeeze Momentum Indicator."""
    arguments['indicator'] = 'SQZMI'
    return await calculate_indicator(arguments)

async def calculate_mi(arguments: dict) -> ToolResult:
    """MI - Mass Index (Standard)."""
    # Note: 'MASSI' is also Mass Index in Finta? 
    # Let's support MI alias if exists.
    arguments['indicator'] = 'MI'
    return await calculate_indicator(arguments)
