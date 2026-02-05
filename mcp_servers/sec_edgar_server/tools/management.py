
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.sec_edgar_server.tools.core import SecCore, dict_to_result
import os
import glob

async def list_downloaded_filings(arguments: dict) -> ToolResult:
    """
    List files available locally for a ticker.
    """
    try:
        ticker = arguments['ticker']
        f_type = arguments.get('filing_type', "*") # * for all
        
        # Pattern: sec_data/sec-edgar-filings/{ticker}/{type}/{accession}/*.txt
        base_path = os.path.join(SecCore.get_downloader().download_folder, "sec-edgar-filings", ticker)
        
        if not os.path.exists(base_path):
            return dict_to_result([], f"No filings found for {ticker}")
            
        # Recursive glob
        # We want to find the .txt or .html files
        # Structure: ticker/type/accession/primary-document.html (or .txt)
        # sec-edgar-downloader usually saves as .txt (full submission)
        
        pattern = os.path.join(base_path, f_type, "*", "*.txt")
        files = glob.glob(pattern)
        
        results = []
        for f in files:
            # Parse path to get meta
            # .../10-K/0000320193-23-000106/full-submission.txt
            parts = f.split(os.sep)
            try:
                acc = parts[-2]
                ft = parts[-3]
                results.append({"filing_type": ft, "accession": acc, "path": f})
            except:
                results.append({"path": f})
                
        return dict_to_result(results, f"Local Filings: {ticker}")
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def read_filing_content(arguments: dict) -> ToolResult:
    """
    Read content of a filing.
    Args:
        path: Absolute path (from list_downloaded_filings).
        max_chars: Limit output (default 10000).
    """
    try:
        path = arguments['path']
        limit = arguments.get('max_chars', 20000)
        
        if not os.path.exists(path):
             return ToolResult(isError=True, content=[TextContent(text="File not found.")])
             
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(limit)
            
        return ToolResult(content=[TextContent(text=content)])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
