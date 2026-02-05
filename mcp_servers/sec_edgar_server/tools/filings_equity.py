
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.sec_edgar_server.tools.core import SecCore, dict_to_result
import asyncio

async def _download_generic(ticker, f_type, amount, after=None, before=None):
    try:
        dl = SecCore.get_downloader()
        count = await asyncio.to_thread(dl.get, f_type, ticker, limit=amount, after=after, before=before)
        return dict_to_result({"ticker": ticker, "filing": f_type, "downloaded": count}, "Download Success")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

# Annual/Quarterly
async def download_10k(arguments: dict) -> ToolResult:
    return await _download_generic(arguments['ticker'], "10-K", arguments.get('amount', 1), arguments.get('after'), arguments.get('before'))

async def download_10q(arguments: dict) -> ToolResult:
    return await _download_generic(arguments['ticker'], "10-Q", arguments.get('amount', 1), arguments.get('after'), arguments.get('before'))

async def download_8k(arguments: dict) -> ToolResult:
    return await _download_generic(arguments['ticker'], "8-K", arguments.get('amount', 1), arguments.get('after'), arguments.get('before'))

async def download_20f(arguments: dict) -> ToolResult: # Foreign Annual
    return await _download_generic(arguments['ticker'], "20-F", arguments.get('amount', 1))

async def download_6k(arguments: dict) -> ToolResult: # Foreign Report
    return await _download_generic(arguments['ticker'], "6-K", arguments.get('amount', 1))
