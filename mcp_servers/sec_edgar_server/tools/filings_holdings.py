
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.sec_edgar_server.tools.filings_equity import _download_generic

# Institutional Holdings
async def download_13f_hr(arguments: dict) -> ToolResult:
    return await _download_generic(arguments['ticker'], "13F-HR", arguments.get('amount', 1))

async def download_13f_nt(arguments: dict) -> ToolResult:
    return await _download_generic(arguments['ticker'], "13F-NT", arguments.get('amount', 1))

# Insider Trading
async def download_form_4(arguments: dict) -> ToolResult: # Change in ownership
    return await _download_generic(arguments['ticker'], "4", arguments.get('amount', 1))

async def download_form_3(arguments: dict) -> ToolResult: # Initial statement
    return await _download_generic(arguments['ticker'], "3", arguments.get('amount', 1))

async def download_form_5(arguments: dict) -> ToolResult: # Annual statement
    return await _download_generic(arguments['ticker'], "5", arguments.get('amount', 1))

# Beneficial Ownership
async def download_13g(arguments: dict) -> ToolResult:
    return await _download_generic(arguments['ticker'], "SC 13G", arguments.get('amount', 1))

async def download_13d(arguments: dict) -> ToolResult:
    return await _download_generic(arguments['ticker'], "SC 13D", arguments.get('amount', 1))
