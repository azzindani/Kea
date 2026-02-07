
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

from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import (
    ticker, screener, analysis, market_intelligence, funds_and_discovery
)
import structlog

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("yahooquery_server", dependencies=["yahooquery", "pandas"])

# --- Ticker Search Tool (USE FIRST when unsure of ticker symbol) ---
@mcp.tool()
async def search_ticker(query: str, limit: int = 5) -> str:
    """ALWAYS USE THIS FIRST when you don't know the exact stock ticker symbol.
    
    Searches for stock ticker symbols by company name or keywords.
    Example: search_ticker("BCA Bank Indonesia") returns "BBCA.JK"
    
    Args:
        query: Company name or keywords (e.g., "BCA Bank", "Bank Central Asia", "Apple")
        limit: Maximum results to return (default: 5)
    
    Returns:
        Table of matching symbols with name, exchange, and type.
        Use the symbol from the results in subsequent financial API calls.
    """
    return await ticker.search_ticker_handler(query, limit)

# --- Core Ticker Tools ---
@mcp.tool()
async def get_fundamental_snapshot(tickers: str) -> str:
    """Get Price, Key Stats, and Summary Detail for multiple tickers."""
    return await ticker.get_fundamental_snapshot(tickers)

@mcp.tool()
async def get_ownership_report(tickers: str) -> str:
    """Get Major Holders, Insiders, Institutions."""
    return await ticker.get_ownership_report(tickers)

@mcp.tool()
async def get_earnings_report(tickers: str) -> str:
    """Get Earnings history, trend, and calendar events."""
    return await ticker.get_earnings_report(tickers)

@mcp.tool()
async def get_technical_snapshot(tickers: str) -> str:
    """Get Price, Recommendation Trend, and Index Trend."""
    return await ticker.get_technical_snapshot(tickers)

@mcp.tool()
async def get_bulk_financials(tickers: str, module_name: str, frequency: str = "a") -> str:
    """Get Balance Sheet, Cash Flow, or Income Statement.
    Args:
        tickers: Space separated symbols
        module_name: balance_sheet, cash_flow, income_statement
        frequency: a (annual) or q (quarterly)
    """
    return await ticker.get_bulk_financials_handler(tickers, module_name, frequency)

@mcp.tool()
async def get_bulk_options(tickers: str) -> str:
    """Get Option Chain (Limit 100 rows)."""
    return await ticker.get_bulk_options_handler(tickers)

# --- Dynamic Ticker Attributes (Unrolled to a single parameterized tool) ---
@mcp.tool()
async def get_ticker_attribute_bulk(tickers: str, attribute_name: str) -> str:
    """Get any specific attribute from yahooquery Ticker object for multiple tickers.
    Common Attributes:
    - asset_profile, calendar_events, company_officers, corporate_guidance
    - earnings_trend, esg_scores, financial_data, fund_performance
    - grading_history, insider_holders, insider_transactions, institution_ownership
    - key_stats, major_holders, news, page_views, price, quote_type
    - recommendation_trend, sec_filings, share_purchase_activity, summary_detail
    - summary_profile
    """
    # Delegate to the generic handler refactored in ticker.py
    return await ticker.generic_ticker_handler(tickers, attribute_name)

# --- Screener ---
@mcp.tool()
async def screen_market(preset: str = "day_gainers", count: int = 100000) -> str:
    """Get data from predefined screener lists.
    Presets: day_gainers, day_losers, most_actives, cryptocurrencies,
    most_shorted_stocks, undervalued_growth_stocks, growth_technology_stocks, etc.
    """
    return await screener.get_screen_data(preset, count)

# --- Analysis & History ---
@mcp.tool()
async def get_bulk_history(tickers: str, period: str = "1mo", interval: str = "1d") -> str:
    """Bulk Download Historical Data (CSV)."""
    return await analysis.get_history_bulk(tickers, period, interval)

# --- Market Intelligence ---
@mcp.tool()
async def get_trending_symbols(country: str = "united states", count: int = 100000) -> str:
    """Get trending securities for a specific region."""
    return await market_intelligence.get_market_trending(country, count)

# --- Funds & Discovery ---
@mcp.tool()
async def get_fund_holdings(tickers: str) -> str:
    """Get Table of Top Holdings for ETFs/Mutual Funds."""
    return await funds_and_discovery.get_fund_holdings_formatted(tickers)

@mcp.tool()
async def get_fund_sectors(tickers: str) -> str:
    """Get Sector Weightings for Funds."""
    return await funds_and_discovery.get_fund_sector_weightings(tickers)

@mcp.tool()
async def search_instruments(query: str) -> str:
    """Search for ANY financial instrument (Stocks, Forex, Crypto, Bonds)."""
    return await funds_and_discovery.search_instruments(query)

@mcp.tool()
async def get_ticker_news(tickers: str) -> str:
    """Get News for specific tickers."""
    return await funds_and_discovery.get_ticker_news(tickers)

if __name__ == "__main__":
    mcp.run()