
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.sec_edgar_server.tools.filings_equity import _download_generic

# Registration Statements
async def download_s1(arguments: dict) -> ToolResult:
    """IPO Registration Statement."""
    return await _download_generic(arguments['ticker'], "S-1", arguments.get('amount', 1))

async def download_s3(arguments: dict) -> ToolResult:
    """Shelf Registration."""
    return await _download_generic(arguments['ticker'], "S-3", arguments.get('amount', 1))

async def download_s4(arguments: dict) -> ToolResult:
    """Merger Registration."""
    return await _download_generic(arguments['ticker'], "S-4", arguments.get('amount', 1))

# Prospectus
async def download_424b4(arguments: dict) -> ToolResult:
    """Prospectus."""
    return await _download_generic(arguments['ticker'], "424B4", arguments.get('amount', 1))

# Exempt Offerings
async def download_form_d(arguments: dict) -> ToolResult:
    """Private Placement (Exempt Offering)."""
    return await _download_generic(arguments['ticker'], "D", arguments.get('amount', 1))
