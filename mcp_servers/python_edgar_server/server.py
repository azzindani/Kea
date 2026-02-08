
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "edgartools",
#   "mcp",
#   "pandas",
#   "structlog",
# ]
# ///


from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.python_edgar_server.tools import (
    discovery, content, financials, ownership, 
    sections_deep, bulk_analysis, xbrl_deep, funds
)
import structlog
import asyncio

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

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
    """ANALYZES profile. [ACTION]
    
    [RAG Context]
    Get company facts and recent filings.
    Returns JSON string.
    """
    return await run_op(discovery.analyze_company_profile, ticker=ticker)

@mcp.tool()
async def find_filings(ticker: str, form: str = None, limit: int = 100000) -> str:
    """SEARCHES filings. [ACTION]
    
    [RAG Context]
    Find filings by form type.
    Returns list string.
    """
    return await run_op(discovery.find_filings, ticker=ticker, form=form, limit=limit)

# 2. Content
@mcp.tool()
async def get_filing_text(ticker: str, form: str) -> str:
    """FETCHES filing text. [ACTION]
    
    [RAG Context]
    Get full markdown content of a filing.
    Returns text content.
    """
    return await run_op(content.get_filing_text, ticker=ticker, form=form)

@mcp.tool()
async def get_filing_sections(ticker: str, form: str) -> str:
    """LISTS sections. [ACTION]
    
    [RAG Context]
    List available sections (Items) in a filing.
    Returns list string.
    """
    return await run_op(content.get_filing_sections, ticker=ticker, form=form)

# 3. Financials
@mcp.tool()
async def get_financial_statements(ticker: str, statement: str) -> str:
    """FETCHES financials. [ACTION]
    
    [RAG Context]
    Get Income, Balance Sheet, or Cash Flow.
    Returns data table.
    """
    return await run_op(financials.get_financial_statements, ticker=ticker, statement=statement)

@mcp.tool()
async def get_financial_metrics(ticker: str) -> str:
    """FETCHES metrics. [ACTION]
    
    [RAG Context]
    Get key financial metrics.
    Returns JSON string.
    """
    return await run_op(financials.get_key_metrics, ticker=ticker)

# 4. Ownership & Intelligence (Phase 2)
@mcp.tool()
async def get_insider_trades(ticker: str, limit: int = None) -> str:
    """FETCHES insider trades. [ACTION]
    
    [RAG Context]
    Get recent insider trading activity.
    Returns data table.
    """
    return await run_op(ownership.get_insider_trades, ticker=ticker, limit=limit)

@mcp.tool()
async def get_institutional_holdings(ticker: str) -> str:
    """FETCHES holdings. [ACTION]
    
    [RAG Context]
    Get institutional 13F ownership.
    Returns data table.
    """
    return await run_op(ownership.get_institutional_holdings, ticker=ticker)

@mcp.tool()
async def get_filing_section_content(ticker: str, form: str, item: str) -> str:
    """EXTRACTS section. [ACTION]
    
    [RAG Context]
    Get text content of a specific item.
    Returns text content.
    """
    return await run_op(sections_deep.get_filing_section_content, ticker=ticker, form=form, item=item)

# 5. Bulk Analysis (Phase 3)
@mcp.tool()
async def get_bulk_company_facts(tickers: str) -> str:
    """FETCHES bulk facts. [ACTION]
    
    [RAG Context]
    Get metadata for multiple tickers.
    Returns JSON string.
    """
    return await run_op(bulk_analysis.get_bulk_company_facts, tickers=tickers)

@mcp.tool()
async def get_financial_history(ticker: str) -> str:
    """FETCHES history. [ACTION]
    
    [RAG Context]
    Get historical financial data.
    Returns time series data.
    """
    return await run_op(bulk_analysis.get_financial_history, ticker=ticker)

# Phase 4
@mcp.tool()
async def get_xbrl_tag_values(ticker: str, tag: str) -> str:
    """EXTRACTS XBRL tag. [ACTION]
    
    [RAG Context]
    Get values for specific XBRL tag.
    Returns data table.
    """
    return await run_op(xbrl_deep.get_xbrl_tag_values, ticker=ticker, tag=tag)

@mcp.tool()
async def search_xbrl_tags(ticker: str, query: str) -> str:
    """SEARCHES XBRL tags. [ACTION]
    
    [RAG Context]
    Find XBRL tags by keyword.
    Returns list of matches.
    """
    return await run_op(xbrl_deep.search_xbrl_tags, ticker=ticker, query=query)

# Phase 5
@mcp.tool()
async def get_fund_portfolio(ticker: str) -> str:
    """FETCHES fund portfolio. [ACTION]
    
    [RAG Context]
    Get 13F portfolio for a fund.
    Returns data table.
    """
    return await run_op(funds.get_fund_portfolio, ticker=ticker)

if __name__ == "__main__":
    mcp.run()