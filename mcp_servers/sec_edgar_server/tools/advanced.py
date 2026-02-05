
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.sec_edgar_server.tools.core import SecCore, dict_to_result
import asyncio

async def download_filing_details(arguments: dict) -> ToolResult:
    """
    Download ALL details (Exhibits, XML, Images) for a filing.
    This creates a folder with many files, not just one .txt.
    """
    try:
        ticker = arguments['ticker']
        f_type = arguments['filing_type']
        amount = arguments.get('amount', 1)
        
        dl = SecCore.get_downloader()
        
        # download_details=True
        count = await asyncio.to_thread(dl.get, f_type, ticker, limit=amount, download_details=True)
        
        return dict_to_result({"ticker": ticker, "filing": f_type, "downloaded": count, "mode": "details"}, "Download Details Success")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
