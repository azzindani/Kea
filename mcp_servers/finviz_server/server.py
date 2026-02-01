
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)



from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import (
    screener, quote, groups, insider, global_markets, calendar_news,
    strategy, charts, financials, bulk_ta
)
from typing import List, Dict, Any, Optional
import structlog

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("finviz_server", dependencies=["finvizfinance", "pandas"])

# --- 1. SCREENER TOOLS ---
@mcp.tool()
async def screen_signal(signal: str, limit: int = 100000) -> Any:
    """
    SIGNAL: Get stocks matching a specific Finviz Signal.
    signal: 'top_gainers', 'new_highs', 'major_news', etc.
    """
    return await screener.get_screener_signal(limit, signal)

# Register Shortcuts for Popular Signals
SIGNALS = screener.get_signal_map()

@mcp.tool()
async def screen_top_gainers(limit: int = 100000) -> Any:
    """SIGNAL: Top Gainers."""
    return await screener.get_screener_signal(limit, "top_gainers")

@mcp.tool()
async def screen_top_losers(limit: int = 100000) -> Any:
    """SIGNAL: Top Losers."""
    return await screener.get_screener_signal(limit, "top_losers")

@mcp.tool()
async def screen_new_highs(limit: int = 100000) -> Any:
    """SIGNAL: New Highs."""
    return await screener.get_screener_signal(limit, "new_highs")

@mcp.tool()
async def screen_major_news(limit: int = 100000) -> Any:
    """SIGNAL: Major News."""
    return await screener.get_screener_signal(limit, "major_news")

@mcp.tool()
async def screen_insider_buying(limit: int = 100000) -> Any:
    """SIGNAL: Insider Buying."""
    return await screener.get_screener_signal(limit, "insider_buying")

# --- 2. QUOTE TOOLS ---
@mcp.tool()
async def get_company_description(ticker: str) -> str:
    """QUOTE: Get company description."""
    return await quote.get_stock_depth(ticker, "description")

@mcp.tool()
async def get_analyst_ratings(ticker: str) -> str:
    """QUOTE: Get analyst ratings."""
    return await quote.get_stock_depth(ticker, "ratings")

@mcp.tool()
async def get_stock_news(ticker: str) -> str:
    """QUOTE: Get latest news headlines for ticker."""
    return await quote.get_stock_depth(ticker, "news")

@mcp.tool()
async def get_insider_trading(ticker: str) -> str:
    """QUOTE: Get insider trading for this ticker."""
    return await quote.get_stock_depth(ticker, "insider")

@mcp.tool()
async def get_fundamental_ratios(ticker: str) -> str:
    """QUOTE: Get fundamental ratios (P/E, EPS, etc)."""
    return await quote.get_stock_depth(ticker, "fundament")

# --- 3. GROUPS ---
@mcp.tool()
async def get_sector_performance() -> str:
    """GROUP: Sector Performance."""
    return await groups.get_group_data("performance", "Sector")

@mcp.tool()
async def get_sector_valuation() -> str:
    """GROUP: Sector Valuation."""
    return await groups.get_group_data("valuation", "Sector")

@mcp.tool()
async def get_industry_performance() -> str:
    """GROUP: Industry Performance."""
    return await groups.get_group_data("performance", "Industry")

@mcp.tool()
async def get_country_performance() -> str:
    """GROUP: Country Performance."""
    return await groups.get_group_data("performance", "Country")

# --- 4. INSIDER MARKET ---
@mcp.tool()
async def get_latest_insider_buys() -> str:
    """INSIDER: Latest Buys."""
    return await insider.get_insider_market("latest_buys")

@mcp.tool()
async def get_latest_insider_sales() -> str:
    """INSIDER: Latest Sales."""
    return await insider.get_insider_market("latest_sales")

@mcp.tool()
async def get_top_insider_buys_week() -> str:
    """INSIDER: Top Week Buys."""
    return await insider.get_insider_market("top_week_buys")

# --- 5. GLOBAL ---
@mcp.tool()
async def get_forex_performance() -> str:
    """GLOBAL: Get Forex performance table."""
    return await global_markets.get_global_performance("forex")

@mcp.tool()
async def get_crypto_performance() -> str:
    """GLOBAL: Get Crypto performance table."""
    return await global_markets.get_global_performance("crypto")

# --- 6. CALENDAR ---
@mcp.tool()
async def get_earnings_calendar(period: str = "This Week") -> str:
    """CALENDAR: Get Earnings for 'This Week', 'Next Week', etc."""
    return await calendar_news.get_earnings_calendar(period)

@mcp.tool()
async def get_market_news_feed(mode: str = "news") -> str:
    """NEWS: Get General Market News or Blogs."""
    return await calendar_news.get_market_news(mode)

# --- 7. STRATEGY ---
@mcp.tool()
async def screen_strategy(strategy: str, limit: int = 100000) -> str:
    """
    STRATEGY: Run a preset strategy screen.
    strategies: 'value_stocks', 'growth_stocks', 'high_yield_dividend', 
                'oversold_bounce', 'new_highs_volume', 'short_squeeze_candidate',
                'undervalued_growth', 'penny_stock_volume'.
    """
    return await strategy.get_strategy_screen(limit, strategy)

# --- 8. ADVANCED ---
@mcp.tool()
async def get_chart_url(ticker: str, timeframe: str = "daily", type: str = "candle") -> str:
    """CHART: Get Finviz Chart image URL."""
    return await charts.get_chart_url(ticker, timeframe, type)

@mcp.tool()
async def get_finviz_statement(ticker: str, statement: str = "I", timeframe: str = "A") -> str:
    """FINANCIALS: Get Income(I)/Balance(B)/Cash(C) Flow table."""
    return await financials.get_finviz_statement(ticker, statement, timeframe)

@mcp.tool()
async def get_technical_table(limit: int = 100000, signal: str = "") -> str:
    """TA: Get Bulk Technical Indicators (RSI, SMA, ATR)."""
    return await bulk_ta.get_technical_table(limit, signal)

if __name__ == "__main__":
    mcp.run()