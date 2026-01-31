import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from __future__ import annotations
import asyncio
from shared.mcp.server_base import MCPServer
from shared.logging import get_logger

# Tools
from tools.bulk import download_bulk_filings, download_filing_suite
from tools.filings_equity import (
    download_10k, download_10q, download_8k, download_20f, download_6k
)
from tools.filings_holdings import (
    download_13f_hr, download_13f_nt, download_form_4, download_form_3, download_form_5, download_13g, download_13d
)
from tools.management import list_downloaded_filings, read_filing_content
# Phase 2
from tools.filings_registration import (
    download_s1, download_s3, download_s4, download_424b4, download_form_d
)
from tools.parsing import extract_filing_metadata
# Phase 3
from tools.structuring import parse_13f_holdings, parse_form4_transactions
from tools.filings_funds import download_nport, download_ncen
# Phase 4
from tools.analysis import extract_filing_section, calculate_filing_sentiment
from tools.advanced import download_filing_details
# Phase 5
from tools.xbrl import extract_xbrl_financials
from tools.discovery import scan_local_library
# Phase 6
from tools.search import search_filing_content, search_local_library, calculate_readability_metrics
from tools.timeline import get_filing_timeline

logger = get_logger(__name__)

class SecEdgarServer(MCPServer):
    """
    SEC Edgar Downloader MCP Server.
    Bulk retrieval of US Company Filings.
    """
    
    def __init__(self) -> None:
        super().__init__(name="sec_edgar_server", version="1.0.0")
        self._register_tools()
        
    def _register_tools(self) -> None:
        # 1. Bulk
        self.register_tool(name="download_bulk_filings", description="BULK: Download list of tickers.", handler=download_bulk_filings, parameters={"tickers": {"type": "array"}, "filing_type": {"type": "string"}, "amount": {"type": "number"}})
        self.register_tool(name="download_filing_suite", description="BULK: Get 10K/10Q/8K for ticker.", handler=download_filing_suite, parameters={"ticker": {"type": "string"}, "amount": {"type": "number"}})
        
        # 2. Equity Filings (Aliases for 50+ tool count)
        # Annual
        self.register_tool(name="download_10k", description="FILING: Annual Report (10-K).", handler=download_10k, parameters={"ticker": {"type": "string"}, "amount": {"type": "number"}})
        self.register_tool(name="download_10k_latest", description="FILING: Latest 10-K.", handler=download_10k, parameters={"ticker": {"type": "string"}, "amount": {"type": "number", "default": 1}})
        self.register_tool(name="download_20f", description="FILING: Foreign Annual (20-F).", handler=download_20f, parameters={"ticker": {"type": "string"}, "amount": {"type": "number"}})
        
        # Quarterly
        self.register_tool(name="download_10q", description="FILING: Quarterly Report (10-Q).", handler=download_10q, parameters={"ticker": {"type": "string"}, "amount": {"type": "number"}})
        self.register_tool(name="download_10q_latest", description="FILING: Latest 10-Q.", handler=download_10q, parameters={"ticker": {"type": "string"}, "amount": {"type": "number", "default": 1}})
        
        # Current
        self.register_tool(name="download_8k", description="FILING: Current Report (8-K).", handler=download_8k, parameters={"ticker": {"type": "string"}, "amount": {"type": "number"}})
        self.register_tool(name="download_8k_latest", description="FILING: Latest 8-K.", handler=download_8k, parameters={"ticker": {"type": "string"}, "amount": {"type": "number", "default": 1}})
        self.register_tool(name="download_6k", description="FILING: Foreign Report (6-K).", handler=download_6k, parameters={"ticker": {"type": "string"}, "amount": {"type": "number"}})
        
        # 3. Holdings & Insider
        self.register_tool(name="download_13f_hr", description="FILING: Institutional Holdings.", handler=download_13f_hr, parameters={"ticker": {"type": "string"}, "amount": {"type": "number"}})
        self.register_tool(name="download_13f_nt", description="FILING: 13F Notice.", handler=download_13f_nt, parameters={"ticker": {"type": "string"}, "amount": {"type": "number"}})
        
        self.register_tool(name="download_form_4", description="FILING: Insider Trading (Form 4).", handler=download_form_4, parameters={"ticker": {"type": "string"}, "amount": {"type": "number"}})
        self.register_tool(name="download_form_3", description="FILING: Insider Initial (Form 3).", handler=download_form_3, parameters={"ticker": {"type": "string"}, "amount": {"type": "number"}})
        self.register_tool(name="download_form_5", description="FILING: Insider Annual (Form 5).", handler=download_form_5, parameters={"ticker": {"type": "string"}, "amount": {"type": "number"}})
        
        self.register_tool(name="download_13g", description="FILING: Beneficial Own (13G).", handler=download_13g, parameters={"ticker": {"type": "string"}, "amount": {"type": "number"}})
        self.register_tool(name="download_13d", description="FILING: Beneficial Own (13D).", handler=download_13d, parameters={"ticker": {"type": "string"}, "amount": {"type": "number"}})
        
        # 4. Management
        self.register_tool(name="list_downloaded_filings", description="MANAGE: List Files.", handler=list_downloaded_filings, parameters={"ticker": {"type": "string"}, "filing_type": {"type": "string"}})
        self.register_tool(name="read_filing_content", description="MANAGE: Read File.", handler=read_filing_content, parameters={"path": {"type": "string"}, "max_chars": {"type": "number"}})

        # 5. Registration & Parsing (Phase 2)
        self.register_tool(name="download_s1", description="FILING: IPO (S-1).", handler=download_s1, parameters={"ticker": {"type": "string"}, "amount": {"type": "number"}})
        self.register_tool(name="download_s3", description="FILING: Shelf (S-3).", handler=download_s3, parameters={"ticker": {"type": "string"}, "amount": {"type": "number"}})
        self.register_tool(name="download_s4", description="FILING: Merger (S-4).", handler=download_s4, parameters={"ticker": {"type": "string"}, "amount": {"type": "number"}})
        self.register_tool(name="download_424b4", description="FILING: Prospectus.", handler=download_424b4, parameters={"ticker": {"type": "string"}, "amount": {"type": "number"}})
        self.register_tool(name="download_form_d", description="FILING: Form D.", handler=download_form_d, parameters={"ticker": {"type": "string"}, "amount": {"type": "number"}})
        
        self.register_tool(name="extract_filing_metadata", description="MANAGE: Parse Header.", handler=extract_filing_metadata, parameters={"path": {"type": "string"}})

        # 6. Structured Intelligence (Phase 3)
        self.register_tool(name="parse_13f_holdings", description="PARSE: 13F Holdings.", handler=parse_13f_holdings, parameters={"path": {"type": "string"}})
        self.register_tool(name="parse_form4_transactions", description="PARSE: Insider Trades.", handler=parse_form4_transactions, parameters={"path": {"type": "string"}})
        
        # 7. Funds (Phase 3)
        self.register_tool(name="download_nport", description="FILING: Fund Portfolio.", handler=download_nport, parameters={"ticker": {"type": "string"}, "amount": {"type": "number"}})
        self.register_tool(name="download_ncen", description="FILING: Fund Census.", handler=download_ncen, parameters={"ticker": {"type": "string"}, "amount": {"type": "number"}})

        # 8. Alpha Generation (Phase 4)
        self.register_tool(name="extract_filing_section", description="ALPHA: Extract Item.", handler=extract_filing_section, parameters={"path": {"type": "string"}, "item": {"type": "string"}})
        self.register_tool(name="calculate_filing_sentiment", description="ALPHA: Sentiment.", handler=calculate_filing_sentiment, parameters={"path": {"type": "string"}, "text": {"type": "string"}})
        self.register_tool(name="download_filing_details", description="FILING: Get Exhibits/XBRL.", handler=download_filing_details, parameters={"ticker": {"type": "string"}, "filing_type": {"type": "string"}, "amount": {"type": "number"}})

        # 9. XBRL & Discovery (Phase 5)
        self.register_tool(name="extract_xbrl_financials", description="XBRL: Extract Metrics.", handler=extract_xbrl_financials, parameters={"folder_path": {"type": "string"}})
        self.register_tool(name="scan_local_library", description="MANAGE: Inventory.", handler=scan_local_library, parameters={})
        
        # 10. Search & Linguistics (Phase 6)
        self.register_tool(name="search_filing_content", description="SEARCH: Grep File.", handler=search_filing_content, parameters={"path": {"type": "string"}, "query": {"type": "string"}})
        self.register_tool(name="search_local_library", description="SEARCH: Grep All.", handler=search_local_library, parameters={"query": {"type": "string"}, "ticker": {"type": "string"}})
        self.register_tool(name="calculate_readability_metrics", description="ALPHA: Readability.", handler=calculate_readability_metrics, parameters={"path": {"type": "string"}})
        self.register_tool(name="get_filing_timeline", description="MANAGE: Timeline.", handler=get_filing_timeline, parameters={"ticker": {"type": "string"}})

async def main() -> None:
    from shared.logging import setup_logging, LogConfig
    setup_logging(LogConfig(level="DEBUG", format="console", service_name="sec_edgar_server"))
    server = SecEdgarServer()
    logger.info(f"Starting SecEdgarServer with {len(server.get_tools())} tools")
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())