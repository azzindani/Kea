
from shared.mcp.protocol import ToolResult, TextContent
from mcp_servers.sec_edgar_server.tools.core import SecCore, dict_to_result
import os

async def get_filing_timeline(arguments: dict) -> ToolResult:
    """
    Get a sorted timeline of all filings for a ticker.
    Detects dates from folder names or filenames.
    """
    ticker = arguments['ticker']
    base_dir = os.path.join(SecCore.get_downloader().download_folder, "sec-edgar-filings", ticker)
    
    if not os.path.exists(base_dir): return dict_to_result([], "No data found")
    
    timeline = []
    
    # Walk: folder structure is Type/Accession
    # Accession often contains date? No. Accession is CIK-YY-SEQ.
    # We must use metadata parsing OR filesystem creation time.
    # Or just return list structured by type.
    
    # Let's try to extract date from a header file if available, or just list accessions.
    # Accession: 0000320193-23-000106. The '23' is the year.
    
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            if f.endswith(".txt"):
                # We have a filing.
                # Path: .../10-K/0000.../full-submission.txt
                parts = root.split(os.sep)
                accession = parts[-1]
                f_type = parts[-2]
                
                # Try to guess year from accession
                year_short = "Unknown"
                if len(accession) > 15:
                    mid = accession.split("-")[1]
                    if len(mid) == 2: year_short = "20" + mid
                    
                path = os.path.join(root, f)
                timeline.append({
                    "type": f_type,
                    "accession": accession,
                    "estimated_year": year_short,
                    "path": path
                })
                
    # Sort by year descending (approx)
    timeline.sort(key=lambda x: x['estimated_year'], reverse=True)
    
    return dict_to_result(timeline, f"Filing Timeline: {ticker}")
