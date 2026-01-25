
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.sec_edgar_server.tools.filings_equity import _download_generic

async def download_nport(arguments: dict) -> ToolResult:
    """Monthly Portfolio Investments (Funds)."""
    return await _download_generic(arguments['ticker'], "N-PORT", arguments.get('amount', 1))

async def download_ncen(arguments: dict) -> ToolResult:
    """Annual Fund Census."""
    return await _download_generic(arguments['ticker'], "N-CEN", arguments.get('amount', 1))
