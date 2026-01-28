from mcp.server.fastmcp import FastMCP, Image
from mcp_servers.yfinance_server.tools import (
    charts, market, financials, holders, analysis, options, discovery, aggregators
)
import structlog
from typing import List, Dict, Any, Optional
import yfinance as yf

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("yfinance_server", dependencies=["yfinance", "pandas", "numpy", "matplotlib", "scipy"])

# --- Market Tools ---
@mcp.tool()
async def get_current_price(ticker: str) -> str:
    """Get price snapshot."""
    return await market.get_current_price(ticker)

@mcp.tool()
async def get_market_cap(ticker: str) -> str:
    """Get Market Cap."""
    return await market.get_market_cap(ticker)

@mcp.tool()
async def get_pe_ratio(ticker: str) -> str:
    """Get Trailing PE Ratio."""
    return await market.get_pe_ratio(ticker)

@mcp.tool()
async def get_volume(ticker: str) -> str:
    """Get recent volume."""
    return await market.get_volume(ticker)

@mcp.tool()
async def get_beta(ticker: str) -> str:
    """Get Beta (Volatility)."""
    return await market.get_beta(ticker)

@mcp.tool()
async def get_quote_metadata(ticker: str) -> str:
    """Get Bid/Ask/Currency."""
    return await market.get_quote_metadata(ticker)

@mcp.tool()
async def get_bulk_historical_data(tickers: str, period: str = "1mo", interval: str = "1d") -> str:
    """Get history for multiple tickers (CSV).
    Args:
        tickers: Space separated list of tickers
        period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    """
    return await market.get_bulk_historical_data(tickers, period, interval)

# --- Financials ---
@mcp.tool()
async def get_income_statement_annual(ticker: str) -> str:
    """Annual Income Statement."""
    return await financials.get_income_statement_annual(ticker)

@mcp.tool()
async def get_income_statement_quarterly(ticker: str) -> str:
    """Quarterly Income Statement."""
    return await financials.get_income_statement_quarterly(ticker)

@mcp.tool()
async def get_balance_sheet_annual(ticker: str) -> str:
    """Annual Balance Sheet."""
    return await financials.get_balance_sheet_annual(ticker)

@mcp.tool()
async def get_balance_sheet_quarterly(ticker: str) -> str:
    """Quarterly Balance Sheet."""
    return await financials.get_balance_sheet_quarterly(ticker)

@mcp.tool()
async def get_cash_flow_annual(ticker: str) -> str:
    """Annual Cash Flow."""
    return await financials.get_cash_flow_annual(ticker)

@mcp.tool()
async def get_cash_flow_quarterly(ticker: str) -> str:
    """Quarterly Cash Flow."""
    return await financials.get_cash_flow_quarterly(ticker)

# --- Holders ---
@mcp.tool()
async def get_major_holders(ticker: str) -> str:
    """Breakdown of Insiders vs Institutions."""
    return await holders.get_major_holders_breakdown(ticker)

@mcp.tool()
async def get_institutional_holders(ticker: str) -> str:
    """Top Institutional Holders."""
    return await holders.get_institutional_holders(ticker)

@mcp.tool()
async def get_mutual_funds(ticker: str) -> str:
    """Top Mutual Funds."""
    return await holders.get_mutual_fund_holders(ticker)

@mcp.tool()
async def get_insider_transactions(ticker: str) -> str:
    """Recent Insider Trading."""
    return await holders.get_insider_transactions(ticker)

@mcp.tool()
async def get_insider_roster(ticker: str) -> str:
    """Key Executives/Holders."""
    return await holders.get_insider_roster(ticker)

# --- Analysis ---
@mcp.tool()
async def get_analyst_ratings(ticker: str) -> str:
    """Buy/Sell/Hold Ratings."""
    return await analysis.get_analyst_recommendations(ticker)

@mcp.tool()
async def get_price_targets(ticker: str) -> str:
    """High/Low/Mean targets."""
    return await analysis.get_price_targets(ticker)

@mcp.tool()
async def get_upgrades_downgrades(ticker: str) -> str:
    """Recent Analyst Actions."""
    return await analysis.get_upgrades_downgrades(ticker)

@mcp.tool()
async def get_earnings_calendar(ticker: str) -> str:
    """Upcoming Earnings Dates."""
    return await analysis.get_earnings_calendar(ticker)

@mcp.tool()
async def get_dividends_history(ticker: str) -> str:
    """Dividend Payment History."""
    return await analysis.get_dividends_history(ticker)

@mcp.tool()
async def get_splits_history(ticker: str) -> str:
    """Stock Splits History."""
    return await analysis.get_splits_history(ticker)

@mcp.tool()
async def calculate_indicators(ticker: str, indicators: List[str], period: str = "1y") -> str:
    """Technical Analysis (SMA, RSI, MACD).
    Args:
        indicators: List of: sma, ema, rsi, macd, bbands
    """
    return await analysis.calculate_indicators(ticker, indicators, period=period)

# --- Charts ---
@mcp.tool()
async def get_price_chart(ticker: str, period: str = "1y") -> Image:
    """Generate Price Chart (Image)."""
    return await charts.get_price_chart(ticker, period)

# --- Options ---
@mcp.tool()
async def get_options_chain(ticker: str, date: str) -> str:
    """Get Option Chain."""
    return await options.get_options_chain(ticker, date)

@mcp.tool()
async def get_option_expirations(ticker: str) -> str:
    """Get Option Expirations."""
    return await options.get_option_expirations(ticker)

# --- Aggregators ---
@mcp.tool()
async def scan_country(country_code: str) -> str:
    """Scan entire country."""
    return await discovery.scan_country(country_code)

@mcp.tool()
async def get_full_report(ticker: str) -> str:
    """Full aggregated report."""
    return await aggregators.get_full_ticker_report(ticker)

# --- Dynamic Info Tool ---
@mcp.tool()
async def get_ticker_info(ticker: str, key: str) -> str:
    """Get any specific metric from yfinance info.
    Keys: enterpriseValue, forwardPE, pegRatio, priceToBook, returnOnEquity, 
    totalRevenue, revenueGrowth, shortRatio, etc.
    """
    try:
        val = yf.Ticker(ticker).info.get(key, "N/A")
        return str(val)
    except:
        return "N/A"

if __name__ == "__main__":
    mcp.run()
