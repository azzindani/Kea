
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.sec_edgar_server.tools.core import SecCore, dict_to_result
import asyncio

async def download_bulk_filings(arguments: dict) -> ToolResult:
    """
    Download filings for multiple tickers.
    Args:
        tickers: List of strings.
        filing_type: "10-K", "10-Q", "8-K", etc.
        amount: Number to download per ticker (default 1).
        after_date: "YYYY-MM-DD"
        before_date: "YYYY-MM-DD"
    """
    try:
        tickers = arguments.get("tickers", [])
        f_type = arguments.get("filing_type", "10-K")
        amount = arguments.get("amount", 100)
        after = arguments.get("after_date")
        before = arguments.get("before_date")
        
        dl = SecCore.get_downloader()
        results = []
        
        # Helper to run blocking download in thread
        def _download(t, ft, n, aft, bef):
            # args for get method: filing_type, ticker_or_cik, limit, after, before, include_amends, download_details
            # sec-edgar-downloader signature: get(filing_type, ticker_or_cik, limit=None, after=None, before=None, include_amends=False, download_details=False)
            return dl.get(ft, t, limit=n, after=aft, before=bef)

        for ticker in tickers:
            try:
                # Run sync download in executor to avoid blocking even loop entirely (though file I/O is heavy)
                # Actually, wrapping in to_thread is good practice.
                count = await asyncio.to_thread(_download, ticker, f_type, amount, after, before)
                results.append({"ticker": ticker, "filing": f_type, "downloaded": count, "status": "success"})
            except Exception as e:
                results.append({"ticker": ticker, "error": str(e), "status": "failed"})
                
        return dict_to_result({"results": results}, "Bulk Download Report")
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def download_filing_suite(arguments: dict) -> ToolResult:
    """
    Download a 'Suite' of filings for one ticker (10-K, 10-Q, 8-K).
    """
    try:
        ticker = arguments['ticker']
        amount = arguments.get('amount', 100)
        
        dl = SecCore.get_downloader()
        
        def _dl_suite():
            c1 = dl.get("10-K", ticker, limit=amount)
            c2 = dl.get("10-Q", ticker, limit=amount)
            c3 = dl.get("8-K", ticker, limit=amount)
            return {"10-K": c1, "10-Q": c2, "8-K": c3}

        res = await asyncio.to_thread(_dl_suite)
        return dict_to_result(res, f"Suite Download: {ticker}")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
