
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# Ensure current directory is in python path for local imports
sys.path.append(str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
from typing import List, Optional
import structlog

# Import tool implementations
from tools.bulk import download_bulk_filings, download_filing_suite
from tools.filings_equity import (
    download_10k, download_10q, download_8k, download_20f, download_6k
)
from tools.filings_holdings import (
    download_13f_hr, download_13f_nt, download_form_4, download_form_3, download_form_5, download_13g, download_13d
)
from tools.management import list_downloaded_filings, read_filing_content
from tools.filings_registration import (
    download_s1, download_s3, download_s4, download_424b4, download_form_d
)
from tools.parsing import extract_filing_metadata
from tools.structuring import parse_13f_holdings, parse_form4_transactions
from tools.filings_funds import download_nport, download_ncen
from tools.analysis import extract_filing_section, calculate_filing_sentiment
from tools.advanced import download_filing_details
from tools.xbrl import extract_xbrl_financials
from tools.discovery import scan_local_library
from tools.search import search_filing_content, search_local_library, calculate_readability_metrics
from tools.timeline import get_filing_timeline

logger = structlog.get_logger()

# Create the FastMCP server
    dependencies=["sec-edgar-downloader", "pandas", "beautifulsoup4", "lxml", "textblob"]
)

# --- PATCH FOR PYRATE-LIMITER v3+ ---
# sec-edgar-downloader uses 'raise_when_fail' kwarg which was removed in pyrate-limiter v3.
# We monkey-patch Limiter to accept and ignore it.
try:
    from pyrate_limiter import Limiter
    original_init = Limiter.__init__

    def patched_init(self, *args, **kwargs):
        if 'raise_when_fail' in kwargs:
            kwargs.pop('raise_when_fail')
        original_init(self, *args, **kwargs)

    Limiter.__init__ = patched_init
except ImportError:
    pass
# ------------------------------------


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
    """BULK: Download filings for multiple tickers.
    
    Args:
        tickers: List of ticker symbols
        filing_type: "10-K", "10-Q", "8-K", etc.
        amount: Number to download per ticker
        after_date: Filter after this date (YYYY-MM-DD)
        before_date: Filter before this date (YYYY-MM-DD)
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
    """BULK: Get 10K/10Q/8K for a single ticker."""
    result = await download_filing_suite({"ticker": ticker, "amount": amount})
    return _extract_text(result)


# =============================================================================
# EQUITY FILINGS - Annual
# =============================================================================
@mcp.tool()
async def get_10k(ticker: str, amount: int = 1) -> str:
    """FILING: Download Annual Report (10-K)."""
    result = await download_10k({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_10k_latest(ticker: str) -> str:
    """FILING: Download Latest 10-K."""
    result = await download_10k({"ticker": ticker, "amount": 1})
    return _extract_text(result)


@mcp.tool()
async def get_20f(ticker: str, amount: int = 1) -> str:
    """FILING: Download Foreign Annual Report (20-F)."""
    result = await download_20f({"ticker": ticker, "amount": amount})
    return _extract_text(result)


# =============================================================================
# EQUITY FILINGS - Quarterly
# =============================================================================
@mcp.tool()
async def get_10q(ticker: str, amount: int = 1) -> str:
    """FILING: Download Quarterly Report (10-Q)."""
    result = await download_10q({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_10q_latest(ticker: str) -> str:
    """FILING: Download Latest 10-Q."""
    result = await download_10q({"ticker": ticker, "amount": 1})
    return _extract_text(result)


# =============================================================================
# EQUITY FILINGS - Current Reports
# =============================================================================
@mcp.tool()
async def get_8k(ticker: str, amount: int = 1) -> str:
    """FILING: Download Current Report (8-K)."""
    result = await download_8k({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_8k_latest(ticker: str) -> str:
    """FILING: Download Latest 8-K."""
    result = await download_8k({"ticker": ticker, "amount": 1})
    return _extract_text(result)


@mcp.tool()
async def get_6k(ticker: str, amount: int = 1) -> str:
    """FILING: Download Foreign Report (6-K)."""
    result = await download_6k({"ticker": ticker, "amount": amount})
    return _extract_text(result)


# =============================================================================
# HOLDINGS & INSIDER FILINGS
# =============================================================================
@mcp.tool()
async def get_13f_hr(ticker: str, amount: int = 1) -> str:
    """FILING: Download Institutional Holdings (13F-HR)."""
    result = await download_13f_hr({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_13f_nt(ticker: str, amount: int = 1) -> str:
    """FILING: Download 13F Notice (13F-NT)."""
    result = await download_13f_nt({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_form_4(ticker: str, amount: int = 1) -> str:
    """FILING: Download Insider Trading (Form 4)."""
    result = await download_form_4({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_form_3(ticker: str, amount: int = 1) -> str:
    """FILING: Download Initial Insider Statement (Form 3)."""
    result = await download_form_3({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_form_5(ticker: str, amount: int = 1) -> str:
    """FILING: Download Annual Insider Statement (Form 5)."""
    result = await download_form_5({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_13g(ticker: str, amount: int = 1) -> str:
    """FILING: Download Beneficial Ownership (Schedule 13G)."""
    result = await download_13g({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_13d(ticker: str, amount: int = 1) -> str:
    """FILING: Download Beneficial Ownership (Schedule 13D)."""
    result = await download_13d({"ticker": ticker, "amount": amount})
    return _extract_text(result)


# =============================================================================
# FILE MANAGEMENT
# =============================================================================
@mcp.tool()
async def list_filings(ticker: str, filing_type: Optional[str] = None) -> str:
    """MANAGE: List downloaded filings for a ticker."""
    result = await list_downloaded_filings({"ticker": ticker, "filing_type": filing_type})
    return _extract_text(result)


@mcp.tool()
async def read_filing(path: str, max_chars: int = 100000) -> str:
    """MANAGE: Read the content of a filing file."""
    result = await read_filing_content({"path": path, "max_chars": max_chars})
    return _extract_text(result)


# =============================================================================
# REGISTRATION FILINGS
# =============================================================================
@mcp.tool()
async def get_s1(ticker: str, amount: int = 1) -> str:
    """FILING: Download IPO Registration (S-1)."""
    result = await download_s1({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_s3(ticker: str, amount: int = 1) -> str:
    """FILING: Download Shelf Registration (S-3)."""
    result = await download_s3({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_s4(ticker: str, amount: int = 1) -> str:
    """FILING: Download Merger Registration (S-4)."""
    result = await download_s4({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_424b4(ticker: str, amount: int = 1) -> str:
    """FILING: Download Prospectus (424B4)."""
    result = await download_424b4({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_form_d(ticker: str, amount: int = 1) -> str:
    """FILING: Download Form D (Exempt Offering)."""
    result = await download_form_d({"ticker": ticker, "amount": amount})
    return _extract_text(result)


# =============================================================================
# PARSING & METADATA
# =============================================================================
@mcp.tool()
async def parse_filing_metadata(path: str) -> str:
    """PARSE: Extract header metadata from a filing."""
    result = await extract_filing_metadata({"path": path})
    return _extract_text(result)


@mcp.tool()
async def parse_13f_holdings_table(path: str) -> str:
    """PARSE: Extract holdings table from 13F filing."""
    result = await parse_13f_holdings({"path": path})
    return _extract_text(result)


@mcp.tool()
async def parse_form4_transactions_table(path: str) -> str:
    """PARSE: Extract transactions from Form 4 filing."""
    result = await parse_form4_transactions({"path": path})
    return _extract_text(result)


# =============================================================================
# FUND FILINGS
# =============================================================================
@mcp.tool()
async def get_nport(ticker: str, amount: int = 1) -> str:
    """FILING: Download Fund Portfolio Report (N-PORT)."""
    result = await download_nport({"ticker": ticker, "amount": amount})
    return _extract_text(result)


@mcp.tool()
async def get_ncen(ticker: str, amount: int = 1) -> str:
    """FILING: Download Fund Census Report (N-CEN)."""
    result = await download_ncen({"ticker": ticker, "amount": amount})
    return _extract_text(result)


# =============================================================================
# ALPHA GENERATION / ANALYSIS
# =============================================================================
@mcp.tool()
async def get_filing_section(path: str, item: str) -> str:
    """ALPHA: Extract a specific section from a filing (e.g., Item 1, Item 7)."""
    result = await extract_filing_section({"path": path, "item": item})
    return _extract_text(result)


@mcp.tool()
async def get_filing_sentiment(path: str = "", text: str = "") -> str:
    """ALPHA: Calculate sentiment score for filing text.
    
    Provide either a path to a filing or the text directly.
    """
    result = await calculate_filing_sentiment({"path": path, "text": text})
    return _extract_text(result)


@mcp.tool()
async def get_filing_details(ticker: str, filing_type: str = "10-K", amount: int = 1) -> str:
    """FILING: Download filing with exhibits and XBRL attachments."""
    result = await download_filing_details({"ticker": ticker, "filing_type": filing_type, "amount": amount})
    return _extract_text(result)


# =============================================================================
# XBRL & DISCOVERY
# =============================================================================
@mcp.tool()
async def get_xbrl_financials(folder_path: str) -> str:
    """XBRL: Extract structured financial metrics from XBRL folder."""
    result = await extract_xbrl_financials({"folder_path": folder_path})
    return _extract_text(result)


@mcp.tool()
async def get_filing_library_inventory() -> str:
    """MANAGE: Scan and inventory all downloaded filings."""
    result = await scan_local_library({})
    return _extract_text(result)


# =============================================================================
# SEARCH & LINGUISTICS
# =============================================================================
@mcp.tool()
async def search_in_filing(path: str, query: str) -> str:
    """SEARCH: Search within a specific filing for text."""
    result = await search_filing_content({"path": path, "query": query})
    return _extract_text(result)


@mcp.tool()
async def search_all_filings(query: str, ticker: Optional[str] = None) -> str:
    """SEARCH: Search across all downloaded filings."""
    result = await search_local_library({"query": query, "ticker": ticker})
    return _extract_text(result)


@mcp.tool()
async def get_readability_metrics(path: str) -> str:
    """ALPHA: Calculate readability scores for a filing."""
    result = await calculate_readability_metrics({"path": path})
    return _extract_text(result)


@mcp.tool()
async def get_timeline(ticker: str) -> str:
    """MANAGE: Get timeline of all filings for a ticker."""
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