
import sys
import os
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

# Clear MPLBACKEND before importing matplotlib (Kaggle sets invalid value)
os.environ.pop('MPLBACKEND', None)

# Yfinance Server
# Managed by pyproject.toml

# Ensure current directory is in python path for local imports
# This fixes "ModuleNotFoundError: No module named 'tools'" in some uv environments
sys.path.append(str(Path(__file__).parent))

from shared.mcp.fastmcp import FastMCP, Image
from mcp_servers.yfinance_server.tools import (
    charts, market, financials, holders, analysis, options, discovery, aggregators
)
import structlog
from typing import List, Dict, Any, Optional
import yfinance as yf

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("yfinance_server", dependencies=["yfinance", "pandas", "numpy", "matplotlib", "scipy"])

# --- Market Tools ---
@mcp.tool()
async def get_current_price(ticker: str) -> str:
    """FETCHES current market price. [ACTION]
    
    [RAG Context]
    Returns a realtime snapshot including current price, day high/low, and volume.
    Use this for single-point price checks.
    """
    return await market.get_current_price(ticker)

@mcp.tool()
async def get_market_cap(ticker: str) -> str:
    """FETCHES market capitalization. [ACTION]
    
    [RAG Context]
    Returns the total value of all outstanding shares.
    Useful for comparing company size (Large Cap vs Small Cap).
    """
    return await market.get_market_cap(ticker)

@mcp.tool()
async def get_pe_ratio(ticker: str) -> str:
    """FETCHES P/E ratio. [ACTION]
    
    [RAG Context]
    Price-to-Earnings ratio is a key valuation metric.
    High P/E suggests growth expectations; Low P/E suggests value or distress.
    """
    return await market.get_pe_ratio(ticker)

@mcp.tool()
async def get_volume(ticker: str) -> str:
    """FETCHES trading volume. [ACTION]
    
    [RAG Context]
    Volume indicates trading activity and liquidity. 
    High volume often confirms price trends.
    """
    return await market.get_volume(ticker)

@mcp.tool()
async def get_beta(ticker: str) -> str:
    """FETCHES Beta volatility. [ACTION]
    
    [RAG Context]
    Beta measures volatility relative to the market.
    - Beta > 1.0: More volatile than market (High Risk/High Reward)
    - Beta < 1.0: Less volatile (Defensive)
    """
    return await market.get_beta(ticker)

@mcp.tool()
async def get_quote_metadata(ticker: str) -> str:
    """FETCHES quote metadata. [ACTION]
    
    [RAG Context]
    Returns low-level market data: Bid, Ask, Currency, Exchange Timezone.
    Essential for executing precise trades or currency conversion.
    """
    return await market.get_quote_metadata(ticker)

@mcp.tool()
async def get_bulk_historical_data(tickers: str = None, ticker: str = None, period: str = "1mo", interval: str = "1d") -> str:
    """FETCHES historical data (Bulk). [ACTION]
    
    [RAG Context]
    Args:
        tickers: Space-separated symbols (e.g. "AAPL MSFT BBCA.JK")
        ticker: Singular symbol (alias for tickers)
        period: "1d", "5d", "1mo", "6mo", "1y", "ytd", "max"
        interval: "1m" (7d max), "1h", "1d", "1wk", "1mo"
        
    Returns CSV string with Open/High/Low/Close/Volume for all tickers.
    """
    return await market.get_bulk_historical_data(tickers, ticker, period, interval)

# --- Financials ---
@mcp.tool()
async def get_income_statement_annual(ticker: str) -> str:
    """FETCHES Annual Income Statement. [ACTION]
    
    [RAG Context]
    Standard GAAP/IFRS Income Statement (Annual).
    Key lines: Total Revenue, Gross Profit, operatingIncome, Net Income.
    Use for long-term fundamental analysis.
    """
    return await financials.get_income_statement_annual(ticker)

@mcp.tool()
async def get_income_statement_quarterly(ticker: str) -> str:
    """FETCHES Quarterly Income Statement. [ACTION]
    
    [RAG Context]
    Latest quarterly performance (Q1/Q2/Q3/Q4).
    Use for catching recent trends or seasonality.
    """
    return await financials.get_income_statement_quarterly(ticker)

@mcp.tool()
async def get_balance_sheet_annual(ticker: str) -> str:
    """FETCHES Annual Balance Sheet. [ACTION]
    
    [RAG Context]
    Snapshot of financial health at year-end.
    Key lines: Total Assets, Total Debt, Stockholders Equity, Cash & Equivalents.
    """
    return await financials.get_balance_sheet_annual(ticker)

@mcp.tool()
async def get_balance_sheet_quarterly(ticker: str) -> str:
    """FETCHES Quarterly Balance Sheet. [ACTION]
    
    [RAG Context]
    Most recent snapshot of Assets vs Liabilities.
    Critical for debt-ratio analysis (e.g. Current Ratio).
    """
    return await financials.get_balance_sheet_quarterly(ticker)

@mcp.tool()
async def get_cash_flow_statement_annual(ticker: str) -> str:
    """FETCHES Annual Cash Flow. [ACTION]
    
    [RAG Context]
    Tracks actual cash movement (Operating, Investing, Financing).
    "Free Cash Flow" must be derived from this.
    """
    return await financials.get_cash_flow_statement_annual(ticker)

@mcp.tool()
async def get_cash_flow_statement_quarterly(ticker: str) -> str:
    """FETCHES Quarterly Cash Flow. [ACTION]
    
    [RAG Context]
    Recent cash burn or generation.
    """
    return await financials.get_cash_flow_statement_quarterly(ticker)

# --- Holders ---
@mcp.tool()
async def get_major_holders(ticker: str) -> str:
    """FETCHES major holders breakdown. [ACTION]
    
    [RAG Context]
    Returns % held by insiders and % held by institutions.
    """
    return await holders.get_major_holders_breakdown(ticker)

@mcp.tool()
async def get_institutional_holders(ticker: str) -> str:
    """FETCHES institutional holders. [ACTION]
    
    [RAG Context]
    Shows which big players own the stock (e.g. BlackRock, Vanguard).
    """
    return await holders.get_institutional_holders(ticker)

@mcp.tool()
async def get_mutual_funds(ticker: str) -> str:
    """FETCHES mutual fund holders. [ACTION]
    
    [RAG Context]
    Shows exposure via Mutual Funds.
    """
    return await holders.get_mutual_fund_holders(ticker)

@mcp.tool()
async def get_insider_transactions(ticker: str) -> str:
    """FETCHES insider transactions. [ACTION]
    
    [RAG Context]
    Tracks if executives (CEO/CFO) are buying or dumping stock.
    Strong buy signal if insiders are buying.
    """
    return await holders.get_insider_transactions(ticker)

@mcp.tool()
async def get_insider_roster(ticker: str) -> str:
    """FETCHES insider roster. [ACTION]
    
    [RAG Context]
    Names and Titles of insiders.
    """
    return await holders.get_insider_roster(ticker)

# --- Analysis ---
@mcp.tool()
async def get_analyst_ratings(ticker: str) -> str:
    """FETCHES analyst ratings. [ACTION]
    
    [RAG Context]
    Analyst recommendations (Strong Buy, Buy, Hold, Sell).
    """
    return await analysis.get_analyst_recommendations(ticker)

@mcp.tool()
async def get_price_targets(ticker: str) -> str:
    """FETCHES price targets. [ACTION]
    
    [RAG Context]
    Future price predictions from Wall St analysts.
    """
    return await analysis.get_price_targets(ticker)

@mcp.tool()
async def get_upgrades_downgrades(ticker: str) -> str:
    """FETCHES upgrades/downgrades. [ACTION]
    
    [RAG Context]
    Changes in analyst sentiment (e.g. JP Morgan Upgrades to Overweight).
    """
    return await analysis.get_upgrades_downgrades(ticker)

@mcp.tool()
async def get_earnings_calendar(ticker: str) -> str:
    """FETCHES earnings calendar. [ACTION]
    
    [RAG Context]
    Next earnings call date and EPS estimates.
    """
    return await analysis.get_earnings_calendar(ticker)

@mcp.tool()
async def get_dividends_history(ticker: str) -> str:
    """FETCHES dividend history. [ACTION]
    
    [RAG Context]
    Date and amount of past dividends.
    Used to calculate yield consistency.
    """
    return await analysis.get_dividends_history(ticker)

@mcp.tool()
async def get_splits_history(ticker: str) -> str:
    """FETCHES split history. [ACTION]
    
    [RAG Context]
    Dates of stock splits (e.g. 1:4).
    """
    return await analysis.get_splits_history(ticker)

@mcp.tool()
async def calculate_indicators(ticker: str, indicators: List[str] = ["sma", "rsi"], period: str = "1y", interval: str = "1d") -> str:
    """CALCULATES technical indicators. [ACTION]
    
    [RAG Context]
    Compute technical analysis values.
    Args:
        indicators: List of ["sma", "ema", "rsi", "macd", "bbands"]
        period: Timeframe ("1y", "6mo")
        interval: Data interval ("1d", "1h")
    """
    return await analysis.calculate_indicators(ticker, indicators, period=period, interval=interval)

# --- Charts ---
@mcp.tool()
async def get_price_chart(ticker: str, period: str = "1y") -> Image:
    """GENERATES price chart. [ACTION]
    
    [RAG Context]
    Returns a PNG image of the stock price history.
    Args:
        period: "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"
    """
    return await charts.get_price_chart(ticker, period)

# --- Options ---
@mcp.tool()
async def get_options_chain(ticker: str, date: str = "", limit: int = 10) -> str:
    """FETCHES options chain (Calls/Puts). [ACTION]
    
    [RAG Context]
    Returns strike prices, bid/ask, and volume for options.
    Args:
        date: Expiration date "YYYY-MM-DD" (use get_option_expirations first)
        limit: Number of rows to return (default: 10)
    """
    return await options.get_options_chain(ticker, date, limit=limit)

@mcp.tool()
async def get_option_expirations(ticker: str) -> str:
    """FETCHES option expirations. [ACTION]
    
    [RAG Context]
    Returns list of "YYYY-MM-DD" strings.
    REQUIRED before calling get_options_chain().
    """
    return await options.get_option_expirations(ticker)

# --- Aggregators ---
@mcp.tool()
async def get_tickers_by_country(country_code: str, limit: int = 50) -> str:
    """SEARCHES tickers by country. [ACTION]
    
    [RAG Context]
    Returns a universe of stocks for a region.
    Args:
        country_code: ISO code (e.g. "ID" for Indonesia, "US" for USA).
        limit: Number of tickers to sample for the report (default: 50).
    """
    return await discovery.get_tickers_by_country(country_code, limit=limit)

@mcp.tool()
async def get_full_report(ticker: str) -> str:
    """GENERATES full financial report. [ACTION]
    
    [RAG Context]
    Aggregates Profile, Price, Financials, and Holders into one large text.
    Use this for "Deep Dive" or "Full Analysis" requests to save tool calls.
    """
    return await aggregators.get_full_ticker_report(ticker)

# --- Dynamic Info Tool ---
@mcp.tool()
async def get_ticker_info(ticker: str, key: str = "longName") -> str:
    """EXTRACTS raw metric from info. [ACTION]
    
    [RAG Context]
    Low-level access to the 'info' dictionary.
    Keys: 'enterpriseValue', 'forwardPE', 'pegRatio', 'priceToBook', 'returnOnEquity', 
          'totalRevenue', 'revenueGrowth', 'shortRatio', 'auditRisk', 'boardRisk'.
    """
    try:
        val = yf.Ticker(ticker).info.get(key, "N/A")
        return str(val)
    except:
        return "N/A"

if __name__ == "__main__":
    mcp.run()


# ==========================================
# Compatibility Layer for Tests
# ==========================================
class YfinanceServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
             return list(self.mcp._tool_manager._tools.values())
        return []
