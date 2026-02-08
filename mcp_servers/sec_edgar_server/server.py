
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# Ensure current directory is in python path for local imports
sys.path.append(str(Path(__file__).parent))

# --- PATCH FOR PYRATE-LIMITER v3+ ---
# sec-edgar-downloader uses 'raise_when_fail' kwarg which was removed in pyrate-limiter v3.
# We monkey-patch Limiter to accept and ignore it.
try:
    from pyrate_limiter import Limiter
    original_init = Limiter.__init__

    def patched_init(self, *args, **kwargs):
        if 'raise_when_fail' in kwargs:
            kwargs.pop('raise_when_fail')
        if 'max_delay' in kwargs:
            kwargs.pop('max_delay')
        original_init(self, *args, **kwargs)

    Limiter.__init__ = patched_init
except ImportError:
    pass
# ------------------------------------

from mcp.server.fastmcp import FastMCP
from typing import List, Optional
import structlog

# Import tool implementations
from mcp_servers.sec_edgar_server.tools.bulk import download_bulk_filings, download_filing_suite
from mcp_servers.sec_edgar_server.tools.filings_equity import (
    download_10k, download_10q, download_8k, download_20f, download_6k
)
from mcp_servers.sec_edgar_server.tools.filings_holdings import (
    download_13f_hr, download_13f_nt, download_form_4, download_form_3, download_form_5, download_13g, download_13d
)
from mcp_servers.sec_edgar_server.tools.management import list_downloaded_filings, read_filing_content
from mcp_servers.sec_edgar_server.tools.filings_registration import (
    download_s1, download_s3, download_s4, download_424b4, download_form_d
)
from mcp_servers.sec_edgar_server.tools.parsing import extract_filing_metadata
from mcp_servers.sec_edgar_server.tools.structuring import parse_13f_holdings, parse_form4_transactions
from mcp_servers.sec_edgar_server.tools.filings_funds import download_nport, download_ncen
from mcp_servers.sec_edgar_server.tools.analysis import extract_filing_section, calculate_filing_sentiment
from mcp_servers.sec_edgar_server.tools.advanced import download_filing_details
from mcp_servers.sec_edgar_server.tools.xbrl import extract_xbrl_financials
from mcp_servers.sec_edgar_server.tools.discovery import scan_local_library
from mcp_servers.sec_edgar_server.tools.search import search_filing_content, search_local_library, calculate_readability_metrics
from mcp_servers.sec_edgar_server.tools.timeline import get_filing_timeline

logger = structlog.get_logger()

from shared.logging import setup_logging
setup_logging()

mcp = FastMCP(
    "sec_edgar_server",
    dependencies=["sec-edgar-downloader", "pandas", "beautifulsoup4", "lxml", "textblob"]
)




# =============================================================================
# BULK OPERATIONS
# =============================================================================
@mcp.tool()
async def bulk_download_filings(
    tickers: List[str],
    filing_type: str = "10-K",
    amount: int = 100,
    after_date: Optional[str] = None,
    before_date: Optional[str] = None
) -> str:
    """DOWNLOADS bulk filings. [ACTION]
    
    [RAG Context]
    Download filings for multiple tickers.
    Returns status string.
    """
    result = await download_bulk_filings({
        "tickers": tickers,
        "filing_type": filing_type,
        "amount": amount,
        "after_date": after_date,
        "before_date": before_date
    })
    return _extract_text(result)


@mcp.tool()
async def bulk_download_filing_suite(ticker: str, amount: int = 100) -> str:
    """DOWNLOADS filing suite. [ACTION]
    
    [RAG Context]
    Get 10K/10Q/8K for a single ticker.
    Returns status string.
    """
    result = await download_filing_suite({"ticker": ticker, "amount": amount})
    return _extract_text(result)


# =============================================================================
# EQUITY FILINGS - Annual
# =============================================================================
@mcp.tool()
async def get_10k(ticker: str, amount: int = 1) -> str:
    """DOWNLOADS 10-K. [ACTION]
    
    [RAG Context]
    Download Annual Report (10-K).
    Returns path string.
    """
    result = await download_10k({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_10k_latest(ticker: str) -> str:
    """DOWNLOADS latest 10-K. [ACTION]
    
    [RAG Context]
    Download Latest 10-K.
    Returns path string.
    """
    result = await download_10k({"ticker": ticker, "amount": 1})
    return _extract_text(result)


@mcp.tool()
async def get_20f(ticker: str, amount: int = 1) -> str:
    """DOWNLOADS 20-F. [ACTION]
    
    [RAG Context]
    Download Foreign Annual Report (20-F).
    Returns path string.
    """
    result = await download_20f({"ticker": ticker, "amount": amount})
    return _extract_text(result)


# =============================================================================
# EQUITY FILINGS - Quarterly
# =============================================================================
@mcp.tool()
async def get_10q(ticker: str, amount: int = 1) -> str:
    """DOWNLOADS 10-Q. [ACTION]
    
    [RAG Context]
    Download Quarterly Report (10-Q).
    Returns path string.
    """
    result = await download_10q({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_10q_latest(ticker: str) -> str:
    """DOWNLOADS latest 10-Q. [ACTION]
    
    [RAG Context]
    Download Latest 10-Q.
    Returns path string.
    """
    result = await download_10q({"ticker": ticker, "amount": 1})
    return _extract_text(result)


# =============================================================================
# EQUITY FILINGS - Current Reports
# =============================================================================
@mcp.tool()
async def get_8k(ticker: str, amount: int = 1) -> str:
    """DOWNLOADS 8-K. [ACTION]
    
    [RAG Context]
    Download Current Report (8-K).
    Returns path string.
    """
    result = await download_8k({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_8k_latest(ticker: str) -> str:
    """DOWNLOADS latest 8-K. [ACTION]
    
    [RAG Context]
    Download Latest 8-K.
    Returns path string.
    """
    result = await download_8k({"ticker": ticker, "amount": 1})
    return _extract_text(result)


@mcp.tool()
async def get_6k(ticker: str, amount: int = 1) -> str:
    """DOWNLOADS 6-K. [ACTION]
    
    [RAG Context]
    Download Foreign Report (6-K).
    Returns path string.
    """
    result = await download_6k({"ticker": ticker, "amount": amount})
    return _extract_text(result)


# =============================================================================
# HOLDINGS & INSIDER FILINGS
# =============================================================================
@mcp.tool()
async def get_13f_hr(ticker: str, amount: int = 1) -> str:
    """DOWNLOADS 13F-HR. [ACTION]
    
    [RAG Context]
    Download Institutional Holdings (13F-HR).
    Returns path string.
    """
    result = await download_13f_hr({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_13f_nt(ticker: str, amount: int = 1) -> str:
    """DOWNLOADS 13F-NT. [ACTION]
    
    [RAG Context]
    Download 13F Notice (13F-NT).
    Returns path string.
    """
    result = await download_13f_nt({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_form_4(ticker: str, amount: int = 1) -> str:
    """DOWNLOADS Form 4. [ACTION]
    
    [RAG Context]
    Download Insider Trading (Form 4).
    Returns path string.
    """
    result = await download_form_4({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_form_3(ticker: str, amount: int = 1) -> str:
    """DOWNLOADS Form 3. [ACTION]
    
    [RAG Context]
    Download Initial Insider Statement (Form 3).
    Returns path string.
    """
    result = await download_form_3({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_form_5(ticker: str, amount: int = 1) -> str:
    """DOWNLOADS Form 5. [ACTION]
    
    [RAG Context]
    Download Annual Insider Statement (Form 5).
    Returns path string.
    """
    result = await download_form_5({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_13g(ticker: str, amount: int = 1) -> str:
    """DOWNLOADS 13G. [ACTION]
    
    [RAG Context]
    Download Beneficial Ownership (Schedule 13G).
    Returns path string.
    """
    result = await download_13g({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_13d(ticker: str, amount: int = 1) -> str:
    """DOWNLOADS 13D. [ACTION]
    
    [RAG Context]
    Download Beneficial Ownership (Schedule 13D).
    Returns path string.
    """
    result = await download_13d({"ticker": ticker, "amount": amount})
    return _extract_text(result)


# =============================================================================
# FILE MANAGEMENT
# =============================================================================
# =============================================================================
# FILE MANAGEMENT
# =============================================================================
@mcp.tool()
async def list_filings(ticker: str, filing_type: Optional[str] = None) -> str:
    """LISTS filings. [ACTION]
    
    [RAG Context]
    List downloaded filings for a ticker.
    Returns list string.
    """
    result = await list_downloaded_filings({"ticker": ticker, "filing_type": filing_type})
    return _extract_text(result)


@mcp.tool()
async def read_filing(path: str, max_chars: int = 100000) -> str:
    """READS filing. [ACTION]
    
    [RAG Context]
    Read the content of a filing file.
    Returns text content.
    """
    result = await read_filing_content({"path": path, "max_chars": max_chars})
    return _extract_text(result)


# =============================================================================
# REGISTRATION FILINGS
# =============================================================================
@mcp.tool()
async def get_s1(ticker: str, amount: int = 1) -> str:
    """DOWNLOADS S-1. [ACTION]
    
    [RAG Context]
    Download IPO Registration (S-1).
    Returns path string.
    """
    result = await download_s1({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_s3(ticker: str, amount: int = 1) -> str:
    """DOWNLOADS S-3. [ACTION]
    
    [RAG Context]
    Download Shelf Registration (S-3).
    Returns path string.
    """
    result = await download_s3({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_s4(ticker: str, amount: int = 1) -> str:
    """DOWNLOADS S-4. [ACTION]
    
    [RAG Context]
    Download Merger Registration (S-4).
    Returns path string.
    """
    result = await download_s4({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_424b4(ticker: str, amount: int = 1) -> str:
    """DOWNLOADS 424B4. [ACTION]
    
    [RAG Context]
    Download Prospectus (424B4).
    Returns path string.
    """
    result = await download_424b4({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_form_d(ticker: str, amount: int = 1) -> str:
    """DOWNLOADS Form D. [ACTION]
    
    [RAG Context]
    Download Form D (Exempt Offering).
    Returns path string.
    """
    result = await download_form_d({"ticker": ticker, "amount": amount})
    return _extract_text(result)


# =============================================================================
# PARSING & METADATA
# =============================================================================
@mcp.tool()
async def parse_filing_metadata(path: str) -> str:
    """PARSES metadata. [ACTION]
    
    [RAG Context]
    Extract header metadata from a filing.
    Returns JSON string.
    """
    result = await extract_filing_metadata({"path": path})
    return _extract_text(result)


@mcp.tool()
async def parse_13f_holdings_table(path: str) -> str:
    """PARSES 13F table. [ACTION]
    
    [RAG Context]
    Extract holdings table from 13F filing.
    Returns JSON string.
    """
    result = await parse_13f_holdings({"path": path})
    return _extract_text(result)


@mcp.tool()
async def parse_form4_transactions_table(path: str) -> str:
    """PARSES Form 4 table. [ACTION]
    
    [RAG Context]
    Extract transactions from Form 4 filing.
    Returns JSON string.
    """
    result = await parse_form4_transactions({"path": path})
    return _extract_text(result)


# =============================================================================
# FUND FILINGS
# =============================================================================
@mcp.tool()
async def get_nport(ticker: str, amount: int = 1) -> str:
    """DOWNLOADS N-PORT. [ACTION]
    
    [RAG Context]
    Download Fund Portfolio Report (N-PORT).
    Returns path string.
    """
    result = await download_nport({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_ncen(ticker: str, amount: int = 1) -> str:
    """DOWNLOADS N-CEN. [ACTION]
    
    [RAG Context]
    Download Fund Census Report (N-CEN).
    Returns path string.
    """
    result = await download_ncen({"ticker": ticker, "amount": amount})
    return _extract_text(result)


# =============================================================================
# ALPHA GENERATION / ANALYSIS
# =============================================================================
# =============================================================================
# ALPHA GENERATION / ANALYSIS
# =============================================================================
@mcp.tool()
async def get_filing_section(path: str, item: str) -> str:
    """EXTRACTS section. [ACTION]
    
    [RAG Context]
    Extract a specific section from a filing (e.g., Item 1, Item 7).
    Returns text content.
    """
    result = await extract_filing_section({"path": path, "item": item})
    return _extract_text(result)


@mcp.tool()
async def get_filing_sentiment(path: str = "", text: str = "") -> str:
    """CALCULATES sentiment. [ACTION]
    
    [RAG Context]
    Calculate sentiment score for filing text.
    Returns JSON string with polarity/subjectivity.
    """
    result = await calculate_filing_sentiment({"path": path, "text": text})
    return _extract_text(result)


@mcp.tool()
async def get_filing_details(ticker: str, filing_type: str = "10-K", amount: int = 1) -> str:
    """DOWNLOADS details. [ACTION]
    
    [RAG Context]
    Download filing with exhibits and XBRL attachments.
    Returns path string.
    """
    result = await download_filing_details({"ticker": ticker, "filing_type": filing_type, "amount": amount})
    return _extract_text(result)


# =============================================================================
# XBRL & DISCOVERY
# =============================================================================
@mcp.tool()
async def get_xbrl_financials(folder_path: str) -> str:
    """EXTRACTS XBRL. [ACTION]
    
    [RAG Context]
    Extract structured financial metrics from XBRL folder.
    Returns JSON string.
    """
    result = await extract_xbrl_financials({"folder_path": folder_path})
    return _extract_text(result)


@mcp.tool()
async def get_filing_library_inventory() -> str:
    """INVENTORIES library. [ACTION]
    
    [RAG Context]
    Scan and inventory all downloaded filings.
    Returns JSON string.
    """
    result = await scan_local_library({})
    return _extract_text(result)


# =============================================================================
# SEARCH & LINGUISTICS
# =============================================================================
@mcp.tool()
async def search_in_filing(path: str, query: str) -> str:
    """SEARCHES filing. [ACTION]
    
    [RAG Context]
    Search within a specific filing for text.
    Returns list of matches.
    """
    result = await search_filing_content({"path": path, "query": query})
    return _extract_text(result)


@mcp.tool()
async def search_all_filings(query: str, ticker: Optional[str] = None) -> str:
    """SEARCHES library. [ACTION]
    
    [RAG Context]
    Search across all downloaded filings.
    Returns list of matches.
    """
    result = await search_local_library({"query": query, "ticker": ticker})
    return _extract_text(result)


@mcp.tool()
async def get_readability_metrics(path: str) -> str:
    """CALCULATES readability. [ACTION]
    
    [RAG Context]
    Calculate readability scores (Gunning Fog, etc).
    Returns JSON string.
    """
    result = await calculate_readability_metrics({"path": path})
    return _extract_text(result)


@mcp.tool()
async def get_timeline(ticker: str) -> str:
    """GENERATES timeline. [ACTION]
    
    [RAG Context]
    Get timeline of all filings for a ticker.
    Returns JSON string.
    """
    result = await get_filing_timeline({"ticker": ticker})
    return _extract_text(result)


# =============================================================================
# HELPER
# =============================================================================
def _extract_text(result) -> str:
    """Extract text from ToolResult for FastMCP string return."""
    if hasattr(result, 'content'):
        texts = []
        for c in result.content:
            if hasattr(c, 'text'):
                texts.append(c.text)
        return "\n".join(texts) if texts else str(result)
    return str(result)


if __name__ == "__main__":
    mcp.run()