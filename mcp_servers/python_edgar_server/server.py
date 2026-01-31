# /// script
# dependencies = [
#   "edgartools",
#   "mcp",
#   "pandas",
#   "structlog",
# ]
# ///


from mcp.server.fastmcp import FastMCP
from tools import (
    discovery, content, financials, ownership, 
    sections_deep, bulk_analysis, xbrl_deep, funds
)
import structlog
import asyncio

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("python_edgar_server", dependencies=["edgartools", "pandas"])

async def run_op(op_func, **kwargs):
    """Helper to run legacy tool ops that expect a dict and return ToolResult."""
    try:
        # The tools expect a single 'arguments' dict.
        result = await op_func(kwargs)
        
        # Unwrap ToolResult
        if hasattr(result, 'content') and result.content:
            text_content = ""
            for item in result.content:
                if hasattr(item, 'text'):
                    text_content += item.text + "\n"
            return text_content.strip()
        
        if hasattr(result, 'isError') and result.isError:
            return "Error: Tool returned error status."
            
        return str(result)
    except Exception as e:
        return f"Error executing tool: {e}"

# 1. Discovery
@mcp.tool()
async def analyze_company_profile(ticker: str) -> str:
    """PROFILE: Facts & Recent Filings."""
    return await run_op(discovery.analyze_company_profile, ticker=ticker)

@mcp.tool()
async def find_filings(ticker: str, form: str = None, limit: int = 100000) -> str:
    """SEARCH: Find Filings."""
    return await run_op(discovery.find_filings, ticker=ticker, form=form, limit=limit)

# 2. Content
@mcp.tool()
async def get_filing_text(ticker: str, form: str) -> str:
    """PARSE: Get Markdown Content."""
    return await run_op(content.get_filing_text, ticker=ticker, form=form)

@mcp.tool()
async def get_filing_sections(ticker: str, form: str) -> str:
    """PARSE: List Sections (Items)."""
    return await run_op(content.get_filing_sections, ticker=ticker, form=form)

# 3. Financials
@mcp.tool()
async def get_financial_statements(ticker: str, statement: str) -> str:
    """XBRL: Income/Balance/Cash."""
    return await run_op(financials.get_financial_statements, ticker=ticker, statement=statement)

@mcp.tool()
async def get_financial_metrics(ticker: str) -> str:
    """XBRL: Key Metrics."""
    return await run_op(financials.get_key_metrics, ticker=ticker)

# 4. Ownership & Intelligence (Phase 2)
@mcp.tool()
async def get_insider_trades(ticker: str, limit: int = None) -> str:
    """OWNERSHIP: Insider Forms."""
    return await run_op(ownership.get_insider_trades, ticker=ticker, limit=limit)

@mcp.tool()
async def get_institutional_holdings(ticker: str) -> str:
    """OWNERSHIP: 13F Funds."""
    return await run_op(ownership.get_institutional_holdings, ticker=ticker)

@mcp.tool()
async def get_filing_section_content(ticker: str, form: str, item: str) -> str:
    """PARSE: Get Item Text."""
    return await run_op(sections_deep.get_filing_section_content, ticker=ticker, form=form, item=item)

# 5. Bulk Analysis (Phase 3)
@mcp.tool()
async def get_bulk_company_facts(tickers: str) -> str:
    """BULK: Metadata Map (Comma-sep tickers)."""
    return await run_op(bulk_analysis.get_bulk_company_facts, tickers=tickers)

@mcp.tool()
async def get_financial_history(ticker: str) -> str:
    """BULK: History."""
    return await run_op(bulk_analysis.get_financial_history, ticker=ticker)

# Phase 4
@mcp.tool()
async def get_xbrl_tag_values(ticker: str, tag: str) -> str:
    """XBRL: Deep Tag Extraction."""
    return await run_op(xbrl_deep.get_xbrl_tag_values, ticker=ticker, tag=tag)

@mcp.tool()
async def search_xbrl_tags(ticker: str, query: str) -> str:
    """XBRL: Tag Search."""
    return await run_op(xbrl_deep.search_xbrl_tags, ticker=ticker, query=query)

# Phase 5
@mcp.tool()
async def get_fund_portfolio(ticker: str) -> str:
    """FUNDS: 13F Portfolio."""
    return await run_op(funds.get_fund_portfolio, ticker=ticker)

if __name__ == "__main__":
    mcp.run()
