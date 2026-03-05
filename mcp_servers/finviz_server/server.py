
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)



from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from mcp_servers.finviz_server.tools import (
    screener, quote, groups, insider, global_markets, calendar_news,
    strategy, charts, financials, bulk_ta
)
from typing import List, Dict, Any, Optional
from shared.logging.main import setup_logging, get_logger
setup_logging(force_stderr=True)
logger = get_logger(__name__)

# Create the FastMCP server

mcp = FastMCP("finviz_server", dependencies=["finvizfinance", "pandas"])

# --- 1. SCREENER TOOLS ---
@mcp.tool()
async def screen_signal(signal: str, limit: int = 100000) -> Any:
    """SCREENS stocks by signal. [ACTION]
    
    [RAG Context]
    A versatile "Super Tool" for technical and fundamental stock screening. It filters the entire US equity market based on specific predefined signals from Finviz.
    
    How to Use:
    - 'signal': Choose from 'top_gainers', 'top_losers', 'new_high', 'new_low', 'most_volatile', 'most_active', 'unusual_volume', 'overbought', 'oversold', 'downgrades', 'upgrades', 'earnings_before', 'earnings_after', 'insider_buying', 'insider_selling'.
    
    Keywords: stock screener, technical signal, market filters, equity screening.
    """
    return await screener.get_screener_signal(limit, signal)

# Register Shortcuts for Popular Signals
SIGNALS = screener.get_signal_map()

@mcp.tool()
async def screen_top_gainers(limit: int = 100000) -> Any:
    """SCREENS Top Gainers. [ACTION]
    
    [RAG Context]
    Retrieves a list of stocks with the highest percentage price increase during the current trading session. Essential for momentum trading strategies.
    
    How to Use:
    - Returns a JSON list of stocks including Ticker, Company, Sector, Price, Change, and Volume.
    - Use this to identify stocks with strong upward momentum and 'hot' market sectors.
    
    Keywords: momentum stocks, market leaders, high growth, daily gainers.
    """
    return await screener.get_screener_signal(limit, "top_gainers")

@mcp.tool()
async def screen_top_losers(limit: int = 100000) -> Any:
    """SCREENS Top Losers. [ACTION]
    
    [RAG Context]
    Retrieves a list of stocks with the sharpest percentage price decrease. Useful for identifying 'oversold' bounce candidates or failing companies.
    
    How to Use:
    - Analyzes intraday sell-offs across NYSE, NASDAQ, and AMEX.
    - Check 'get_stock_news' for the tickers found to understand the reason for the drop.
    
    Keywords: oversold stocks, market laggards, daily losers, short-side candidates.
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
    A high-conviction "Super Tool" that filters for stocks where company executives (CEOs, CFOs, Directors) are buying their own company's shares in the open market.
    
    How to Use:
    - Often considered a strong bullish indicator as insiders have the most visibility into the company's future value.
    - Combine with 'get_fundamental_ratios' to verify valuation before investing.
    
    Keywords: insider accumulation, conviction buying, executive trades, smart money flow.
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
    A powerful "Super Tool" for running advanced, automated trading strategies from the Finviz strategy database.
    
    How to Use:
    - 'strategies': 'value_stocks', 'growth_stocks', 'high_yield_dividend', 'oversold_bounce', 'new_highs_volume', 'short_squeeze_candidate'.
    - Returns a list of tickers that meet multiple technical and fundamental criteria for each strategy.
    
    Keywords: investment strategy, stock picks, value growth, strategy engine.
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
    Retrieves high-level accounting data for a public company.
    
    How to Use:
    - 'statement': 'I' (Income Statement), 'B' (Balance Sheet), 'C' (Cash Flow).
    - 'timeframe': 'A' (Annual), 'Q' (Quarterly).
    - Returns columns for Net Income, Total Assets, Revenue, and Operating Cash over time.
    
    Keywords: corporate health, accounting data, revenue report, p&l statement.
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

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class FinvizServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
            return list(self.mcp._tool_manager._tools.values())
        return []



