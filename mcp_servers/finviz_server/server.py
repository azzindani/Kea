
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
from mcp_servers.finviz_server.tools import (
    screener, quote, groups, insider, global_markets, calendar_news,
    strategy, charts, financials, bulk_ta
)
from typing import List, Dict, Any, Optional
import structlog

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("finviz_server", dependencies=["finvizfinance", "pandas"])

# --- 1. SCREENER TOOLS ---
@mcp.tool()
async def screen_signal(signal: str, limit: int = 100000) -> Any:
    """SCREENS stocks by signal. [ACTION]
    
    [RAG Context]
    Get stocks matching a specific Finviz Signal.
    signal: 'top_gainers', 'new_highs', 'major_news', etc.
    """
    return await screener.get_screener_signal(limit, signal)

# Register Shortcuts for Popular Signals
SIGNALS = screener.get_signal_map()

@mcp.tool()
async def screen_top_gainers(limit: int = 100000) -> Any:
    """SCREENS Top Gainers. [ACTION]
    
    [RAG Context]
    Get top gaining stocks.
    Returns JSON list of stocks.
    """
    return await screener.get_screener_signal(limit, "top_gainers")

@mcp.tool()
async def screen_top_losers(limit: int = 100000) -> Any:
    """SCREENS Top Losers. [ACTION]
    
    [RAG Context]
    Get top losing stocks.
    Returns JSON list of stocks.
    """
    return await screener.get_screener_signal(limit, "top_losers")

@mcp.tool()
async def screen_new_highs(limit: int = 100000) -> Any:
    """SCREENS New Highs. [ACTION]
    
    [RAG Context]
    Get stocks making new highs.
    Returns JSON list of stocks.
    """
    return await screener.get_screener_signal(limit, "new_highs")

@mcp.tool()
async def screen_major_news(limit: int = 100000) -> Any:
    """SCREENS Major News. [ACTION]
    
    [RAG Context]
    Get stocks with major news events.
    Returns JSON list of stocks.
    """
    return await screener.get_screener_signal(limit, "major_news")

@mcp.tool()
async def screen_insider_buying(limit: int = 100000) -> Any:
    """SCREENS Insider Buying. [ACTION]
    
    [RAG Context]
    Get stocks with recent insider buying.
    Returns JSON list of stocks.
    """
    return await screener.get_screener_signal(limit, "insider_buying")

# --- 2. QUOTE TOOLS ---
@mcp.tool()
async def get_company_description(ticker: str) -> str:
    """FETCHES company description. [ACTION]
    
    [RAG Context]
    Get company profile and description.
    Returns string.
    """
    return await quote.get_stock_depth(ticker, "description")

@mcp.tool()
async def get_analyst_ratings(ticker: str) -> str:
    """FETCHES analyst ratings. [ACTION]
    
    [RAG Context]
    Get analyst ratings and price targets.
    Returns JSON string.
    """
    return await quote.get_stock_depth(ticker, "ratings")

@mcp.tool()
async def get_stock_news(ticker: str) -> str:
    """FETCHES stock news. [ACTION]
    
    [RAG Context]
    Get latest news headlines for ticker.
    Returns JSON string.
    """
    return await quote.get_stock_depth(ticker, "news")

@mcp.tool()
async def get_insider_trading(ticker: str) -> str:
    """FETCHES insider trading. [ACTION]
    
    [RAG Context]
    Get insider trading history for this ticker.
    Returns JSON string.
    """
    return await quote.get_stock_depth(ticker, "insider")

@mcp.tool()
async def get_fundamental_ratios(ticker: str) -> str:
    """FETCHES fundamental ratios. [ACTION]
    
    [RAG Context]
    Get fundamental ratios (P/E, EPS, etc).
    Returns JSON string.
    """
    return await quote.get_stock_depth(ticker, "fundament")

# --- 3. GROUPS ---
@mcp.tool()
async def get_sector_performance() -> str:
    """FETCHES Sector Performance. [ACTION]
    
    [RAG Context]
    Get performance by sector.
    Returns JSON string.
    """
    return await groups.get_group_data("performance", "Sector")

@mcp.tool()
async def get_sector_valuation() -> str:
    """FETCHES Sector Valuation. [ACTION]
    
    [RAG Context]
    Get valuation metrics by sector.
    Returns JSON string.
    """
    return await groups.get_group_data("valuation", "Sector")

@mcp.tool()
async def get_industry_performance() -> str:
    """FETCHES Industry Performance. [ACTION]
    
    [RAG Context]
    Get performance by industry.
    Returns JSON string.
    """
    return await groups.get_group_data("performance", "Industry")

@mcp.tool()
async def get_country_performance() -> str:
    """FETCHES Country Performance. [ACTION]
    
    [RAG Context]
    Get performance by country.
    Returns JSON string.
    """
    return await groups.get_group_data("performance", "Country")

# --- 4. INSIDER MARKET ---
@mcp.tool()
async def get_latest_insider_buys() -> str:
    """FETCHES latest insider buys. [ACTION]
    
    [RAG Context]
    Get recent insider buying transactions.
    Returns JSON string.
    """
    return await insider.get_insider_market("latest_buys")

@mcp.tool()
async def get_latest_insider_sales() -> str:
    """FETCHES latest insider sales. [ACTION]
    
    [RAG Context]
    Get recent insider selling transactions.
    Returns JSON string.
    """
    return await insider.get_insider_market("latest_sales")

@mcp.tool()
async def get_top_insider_buys_week() -> str:
    """FETCHES top week buys. [ACTION]
    
    [RAG Context]
    Get top insider buys for the week.
    Returns JSON string.
    """
    return await insider.get_insider_market("top_week_buys")

# --- 5. GLOBAL ---
@mcp.tool()
async def get_forex_performance() -> str:
    """FETCHES Forex performance. [ACTION]
    
    [RAG Context]
    Get performance table for Forex pairs.
    Returns JSON string.
    """
    return await global_markets.get_global_performance("forex")

@mcp.tool()
async def get_crypto_performance() -> str:
    """FETCHES Crypto performance. [ACTION]
    
    [RAG Context]
    Get performance table for Crypto pairs.
    Returns JSON string.
    """
    return await global_markets.get_global_performance("crypto")

# --- 6. CALENDAR ---
@mcp.tool()
async def get_earnings_calendar(period: str = "This Week") -> str:
    """FETCHES earnings calendar. [ACTION]
    
    [RAG Context]
    Get Earnings for 'This Week', 'Next Week', etc.
    Returns JSON string.
    """
    return await calendar_news.get_earnings_calendar(period)

@mcp.tool()
async def get_market_news_feed(mode: str = "news") -> str:
    """FETCHES market news. [ACTION]
    
    [RAG Context]
    Get General Market News or Blogs.
    Returns JSON string.
    """
    return await calendar_news.get_market_news(mode)

# --- 7. STRATEGY ---
@mcp.tool()
async def screen_strategy(strategy: str, limit: int = 100000) -> str:
    """SCREENS strategy preset. [ACTION]
    
    [RAG Context]
    Run a preset strategy screen.
    strategies: 'value_stocks', 'growth_stocks', 'high_yield_dividend', 
                'oversold_bounce', 'new_highs_volume', 'short_squeeze_candidate'.
    """
    return await strategy.get_strategy_screen(limit, strategy)

# --- 8. ADVANCED ---
@mcp.tool()
async def get_chart_url(ticker: str, timeframe: str = "daily", type: str = "candle") -> str:
    """FETCHES chart URL. [ACTION]
    
    [RAG Context]
    Get Finviz Chart image URL.
    Returns URL string.
    """
    return await charts.get_chart_url(ticker, timeframe, type)

@mcp.tool()
async def get_finviz_statement(ticker: str, statement: str = "I", timeframe: str = "A") -> str:
    """FETCHES financials. [ACTION]
    
    [RAG Context]
    Get Income(I)/Balance(B)/Cash(C) Flow table.
    Returns JSON string.
    """
    return await financials.get_finviz_statement(ticker, statement, timeframe)

@mcp.tool()
async def get_technical_table(limit: int = 100000, signal: str = "") -> str:
    """FETCHES technical table. [ACTION]
    
    [RAG Context]
    Get Bulk Technical Indicators (RSI, SMA, ATR).
    Returns JSON string.
    """
    return await bulk_ta.get_technical_table(limit, signal)

if __name__ == "__main__":
    mcp.run()