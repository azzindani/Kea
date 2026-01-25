
from __future__ import annotations
import asyncio
from shared.mcp.server_base import MCPServer
from shared.logging import get_logger

# Tools
from mcp_servers.python_edgar_server.tools.discovery import analyze_company_profile, find_filings
from mcp_servers.python_edgar_server.tools.content import get_filing_text, get_filing_sections
from mcp_servers.python_edgar_server.tools.financials import get_financial_statements, get_key_metrics
# Phase 2
from mcp_servers.python_edgar_server.tools.ownership import get_insider_trades, get_institutional_holdings
from mcp_servers.python_edgar_server.tools.sections_deep import get_filing_section_content
# Phase 3
from mcp_servers.python_edgar_server.tools.bulk_analysis import get_bulk_company_facts, get_financial_history
from mcp_servers.python_edgar_server.tools.xbrl_deep import get_xbrl_tag_values, search_xbrl_tags
from mcp_servers.python_edgar_server.tools.funds import get_fund_portfolio

logger = get_logger(__name__)

class PythonEdgarServer(MCPServer):
    """
    Python-Edgar (EdgarTools) MCP Server.
    Object-Oriented Parsing and XBRL Extraction.
    """
    
    def __init__(self) -> None:
        super().__init__(name="python_edgar_server", version="1.0.0")
        self._register_tools()
        
    def _register_tools(self) -> None:
        # 1. Discovery
        self.register_tool(name="analyze_company_profile", description="PROFILE: Facts & Recent Filings.", handler=analyze_company_profile, parameters={"ticker": {"type": "string"}})
        self.register_tool(name="find_filings", description="SEARCH: Find Filings.", handler=find_filings, parameters={"ticker": {"type": "string"}, "form": {"type": "string"}, "limit": {"type": "number"}})
        
        # 2. Content
        self.register_tool(name="get_filing_text", description="PARSE: Get Markdown Content.", handler=get_filing_text, parameters={"ticker": {"type": "string"}, "form": {"type": "string"}})
        self.register_tool(name="get_filing_sections", description="PARSE: List Sections (Items).", handler=get_filing_sections, parameters={"ticker": {"type": "string"}, "form": {"type": "string"}})
        
        # 3. Financials
        self.register_tool(name="get_financial_statements", description="XBRL: Income/Balance/Cash.", handler=get_financial_statements, parameters={"ticker": {"type": "string"}, "statement": {"type": "string"}})
        self.register_tool(name="get_financial_metrics", description="XBRL: Key Metrics.", handler=get_key_metrics, parameters={"ticker": {"type": "string"}})

        # 4. Ownership & Intelligence (Phase 2)
        self.register_tool(name="get_insider_trades", description="OWNERSHIP: Insider Forms.", handler=get_insider_trades, parameters={"ticker": {"type": "string"}, "limit": {"type": "number"}})
        self.register_tool(name="get_institutional_holdings", description="OWNERSHIP: 13F Funds.", handler=get_institutional_holdings, parameters={"ticker": {"type": "string"}})
        self.register_tool(name="get_filing_section_content", description="PARSE: Get Item Text.", handler=get_filing_section_content, parameters={"ticker": {"type": "string"}, "form": {"type": "string"}, "item": {"type": "string"}})

        # 5. Bulk Analysis (Phase 3)
        self.register_tool(name="get_bulk_company_facts", description="BULK: Metadata Map.", handler=get_bulk_company_facts, parameters={"tickers": {"type": "string"}}) # Comma-sep
        self.register_tool(name="get_financial_history", description="BULK: History.", handler=get_financial_history, parameters={"ticker": {"type": "string"}})

        # Phase 4
        self.register_tool(name="get_xbrl_tag_values", description="XBRL: Deep Tag Extraction.", handler=get_xbrl_tag_values, parameters={"ticker": {"type": "string"}, "tag": {"type": "string"}})
        self.register_tool(name="search_xbrl_tags", description="XBRL: Tag Search.", handler=search_xbrl_tags, parameters={"ticker": {"type": "string"}, "query": {"type": "string"}})

        # Phase 5
        self.register_tool(name="get_fund_portfolio", description="FUNDS: 13F Portfolio.", handler=get_fund_portfolio, parameters={"ticker": {"type": "string"}})

async def main() -> None:
    from shared.logging import setup_logging, LogConfig
    setup_logging(LogConfig(level="DEBUG", format="console", service_name="python_edgar_server"))
    server = PythonEdgarServer()
    logger.info(f"Starting PythonEdgarServer with {len(server.get_tools())} tools")
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
