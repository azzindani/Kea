
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# /// script
# dependencies = [
#   "mcp",
#   "pandas",
#   "structlog",
#   "yahooquery",
# ]
# ///

from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.yahooquery_server.tools import (
    ticker, screener, analysis, market_intelligence, funds_and_discovery
)
import structlog

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

mcp = FastMCP("yahooquery_server", dependencies=["yahooquery", "pandas"])

# --- Ticker Search Tool (USE FIRST when unsure of ticker symbol) ---
# --- Ticker Search Tool (USE FIRST when unsure of ticker symbol) ---
@mcp.tool()
async def search_ticker(query: str, limit: int = 5) -> str:
    """SEARCHES for ticker symbols. [ACTION]
    
    [RAG Context]
    ALWAYS USE THIS FIRST when you don't know the exact stock ticker symbol.
    Searches by company name or keywords (e.g., "BCA Bank" -> "BBCA.JK").
    Returns table of matching symbols.
    """
    return await ticker.search_ticker_handler(query, limit)

# --- Core Ticker Tools ---
@mcp.tool()
async def get_fundamental_snapshot(tickers: str) -> str:
    """FETCHES fundamental snapshot. [ACTION]
    
    [RAG Context]
    Get Price, Key Stats, and Summary Detail for multiple tickers.
    Returns JSON string.
    """
    return await ticker.get_fundamental_snapshot(tickers)

@mcp.tool()
async def get_ownership_report(tickers: str) -> str:
    """FETCHES ownership report. [ACTION]
    
    [RAG Context]
    Get Major Holders, Insiders, Institutions.
    Returns JSON string.
    """
    return await ticker.get_ownership_report(tickers)

@mcp.tool()
async def get_earnings_report(tickers: str) -> str:
    """FETCHES earnings report. [ACTION]
    
    [RAG Context]
    Get Earnings history, trend, and calendar events.
    Returns JSON string.
    """
    return await ticker.get_earnings_report(tickers)

@mcp.tool()
async def get_technical_snapshot(tickers: str) -> str:
    """FETCHES technical snapshot. [ACTION]
    
    [RAG Context]
    Get Price, Recommendation Trend, and Index Trend.
    Returns JSON string.
    """
    return await ticker.get_technical_snapshot(tickers)

@mcp.tool()
async def get_bulk_financials(tickers: str, module_name: str, frequency: str = "a") -> str:
    """FETCHES bulk financials. [ACTION]
    
    [RAG Context]
    Get Balance Sheet, Cash Flow, or Income Statement.
    Args:
        tickers: Space separated symbols
        module_name: balance_sheet, cash_flow, income_statement
        frequency: a (annual) or q (quarterly)
    Returns JSON string.
    """
    return await ticker.get_bulk_financials_handler(tickers, module_name, frequency)

@mcp.tool()
async def get_income_statement(ticker_symbol: str, frequency: str = "a") -> str:
    """FETCHES income statement. [ACTION]
    
    [RAG Context]
    Get Income Statement for a specific ticker.
    Args:
        ticker_symbol: e.g. "AAPL"
        frequency: a (annual) or q (quarterly)
    Returns JSON/Markdown string.
    """
    return await ticker.get_income_statement(ticker_symbol, frequency)

@mcp.tool()
async def get_balance_sheet(ticker_symbol: str, frequency: str = "a") -> str:
    """FETCHES balance sheet. [ACTION]
    
    [RAG Context]
    Get Balance Sheet for a specific ticker.
    Args:
        ticker_symbol: e.g. "AAPL"
        frequency: a (annual) or q (quarterly)
    Returns JSON/Markdown string.
    """
    return await ticker.get_balance_sheet(ticker_symbol, frequency)

@mcp.tool()
async def get_cash_flow(ticker_symbol: str, frequency: str = "a") -> str:
    """FETCHES cash flow statement. [ACTION]
    
    [RAG Context]
    Get Cash Flow Statement for a specific ticker.
    Args:
        ticker_symbol: e.g. "AAPL"
        frequency: a (annual) or q (quarterly)
    Returns JSON/Markdown string.
    """
    return await ticker.get_cash_flow(ticker_symbol, frequency)

@mcp.tool()
async def get_bulk_options(tickers: str) -> str:
    """FETCHES bulk options. [ACTION]
    
    [RAG Context]
    Get Option Chain (Limit 100 rows).
    Returns JSON string.
    """
    return await ticker.get_bulk_options_handler(tickers)

# --- Dynamic Ticker Attributes (Unrolled to a single parameterized tool) ---
@mcp.tool()
async def get_ticker_attribute_bulk(tickers: str, attribute_name: str) -> str:
    """FETCHES specific attribute. [ACTION]
    
    [RAG Context]
    Get any specific attribute from yahooquery Ticker object for multiple tickers.
    Common Attributes:
    - asset_profile, calendar_events, company_officers, corporate_guidance
    - earnings_trend, esg_scores, financial_data, fund_performance
    - grading_history, insider_holders, insider_transactions, institution_ownership
    - key_stats, major_holders, news, page_views, price, quote_type
    - recommendation_trend, sec_filings, share_purchase_activity, summary_detail
    - summary_profile
    Returns JSON string.
    """
    # Delegate to the generic handler refactored in ticker.py
    return await ticker.generic_ticker_handler(tickers, attribute_name)

# --- Screener ---
@mcp.tool()
async def screen_market(preset: str = "day_gainers", count: int = 100000) -> str:
    """SCREENS market using preset. [ACTION]
    
    [RAG Context]
    Get data from predefined screener lists.
    Presets: day_gainers, day_losers, most_actives, cryptocurrencies,
    most_shorted_stocks, undervalued_growth_stocks, growth_technology_stocks, etc.
    Returns JSON string.
    """
    return await screener.get_screen_data(preset, count)

# --- Analysis & History ---
@mcp.tool()
async def get_bulk_history(tickers: str, period: str = "1mo", interval: str = "1d") -> str:
    """FETCHES bulk history. [ACTION]
    
    [RAG Context]
    Bulk Download Historical Data (CSV).
    Returns CSV string.
    """
    return await analysis.get_history_bulk(tickers, period, interval)

# --- Market Intelligence ---
@mcp.tool()
async def get_trending_symbols(country: str = "united states", count: int = 100000) -> str:
    """FETCHES trending symbols. [ACTION]
    
    [RAG Context]
    Get trending securities for a specific region.
    Returns JSON string.
    """
    return await market_intelligence.get_market_trending(country, count)

# --- Funds & Discovery ---
@mcp.tool()
async def get_fund_holdings(tickers: str) -> str:
    """FETCHES fund holdings. [ACTION]
    
    [RAG Context]
    Get Table of Top Holdings for ETFs/Mutual Funds.
    Returns JSON string.
    """
    return await funds_and_discovery.get_fund_holdings_formatted(tickers)

@mcp.tool()
async def get_fund_sectors(tickers: str) -> str:
    """FETCHES fund sectors. [ACTION]
    
    [RAG Context]
    Get Sector Weightings for Funds.
    Returns JSON string.
    """
    return await funds_and_discovery.get_fund_sector_weightings(tickers)

@mcp.tool()
async def search_instruments(query: str) -> str:
    """SEARCHES instruments. [ACTION]
    
    [RAG Context]
    Search for ANY financial instrument (Stocks, Forex, Crypto, Bonds).
    Returns JSON string.
    """
    return await funds_and_discovery.search_instruments(query)

@mcp.tool()
async def get_ticker_news(tickers: str) -> str:
    """FETCHES ticker news. [ACTION]
    
    [RAG Context]
    Get News for specific tickers.
    Returns JSON string.
    """
    return await funds_and_discovery.get_ticker_news(tickers)

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class YahooqueryServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []

