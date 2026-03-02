
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
# from mcp_servers.yfinance_server.tools import (
#     charts, market, financials, holders, analysis, options, discovery, aggregators
# )
# Note: Tools will be imported lazily inside each tool function to speed up startup.

import structlog
from typing import List, Dict, Any, Optional
import yfinance as yf

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.main import setup_logging
setup_logging(force_stderr=True)

mcp = FastMCP("yfinance_server", dependencies=["yfinance", "pandas", "numpy", "matplotlib", "scipy"])

# --- Market Tools ---
@mcp.tool()
async def get_current_price(ticker: str) -> str:
    """FETCHES current market price. [ACTION]
    
    [RAG Context]
    Retrieves the most recent realtime market price for a specific financial instrument (stock, ETF, index, or cryptocurrency). 
    This tool provides a snapshot of the current trading session, including the last traded price, daily high and low prices, and total trading volume.
    
    How to Use:
    - Pass a single ticker symbol (e.g., 'AAPL' for Apple, 'BTC-USD' for Bitcoin, or 'BBCA.JK' for Bank Central Asia).
    - Use this for immediate status checks before initiating a trade or when a user asks "what is the price of X?".
    - For comparing multiple tickers, call this tool sequentially or use 'get_bulk_historical_data'.
    
    Arguments:
    - ticker (str): The official symbol used on the exchange. For non-US stocks, include the suffix (e.g., '.L' for London, '.JK' for Jakarta).
    
    Example:
    - Input: ticker="AAPL"
    - Output: "AAPL: 185.92, High: 187.20, Low: 184.50, Volume: 52,000,000"
    
    Keywords: stock price, quote, ticker value, real-time market data, equity price, asset value.
    """
    from mcp_servers.yfinance_server.tools import market
    return await market.get_current_price(ticker)

@mcp.tool()
async def get_market_cap(ticker: str) -> str:
    """FETCHES market capitalization. [ACTION]
    
    [RAG Context]
    A fundamental "Super Tool" for equity valuation and peer comparison. It returns the total dollar market value of a company's outstanding shares, which serves as a definitive indicator of a company's size, risk profile, and investment tier (e.g., Large, Mid, or Small Cap).
    
    How to Use:
    - Crucial for screening companies based on fiscal stability or industry dominance.
    - Used by the Orchestrator to categorize "blue chip" stocks vs "growth" stocks in portfolio analysis.
    
    Keywords: company valuation, market value, equity size, total share value.
    """
    from mcp_servers.yfinance_server.tools import market
    return await market.get_market_cap(ticker)

@mcp.tool()
async def get_pe_ratio(ticker: str) -> str:
    """FETCHES P/E ratio. [ACTION]
    
    [RAG Context]
    Retrieves the Price-to-Earnings (P/E) ratio, which is a primary valuation metric used to determine if a stock is overvalued or undervalued relative to its earnings.
    
    How to Use:
    - A high P/E might indicate that a stock's price is high relative to earnings and possibly overvalued, or that investors are expecting high growth rates in the future.
    - A low P/E might indicate that the stock is undervalued or that it is a "value" play.
    - Always compare P/E ratios within the same industry for accurate context.
    
    Arguments:
    - ticker (str): The ticker symbol.
    
    Example:
    - Input: ticker="NVDA"
    - Output: "Trailing P/E: 75.4, Forward P/E: 35.2"
    
    Keywords: valuation, earnings multiple, overvalued, undervalued, fundamental analysis.
    """
    from mcp_servers.yfinance_server.tools import market
    return await market.get_pe_ratio(ticker)

@mcp.tool()
async def get_volume(ticker: str) -> str:
    """FETCHES trading volume. [ACTION]
    
    [RAG Context]
    Retrieves the number of shares or contracts traded in a security or an entire market during a given period of time.
    
    How to Use:
    - High volume indicates high liquidity and strong interest in the stock at the current price.
    - Use volume to confirm price trends; a price move (up or down) on high volume is considered more significant than one on low volume.
    - Check for "volume spikes" which often precede major news or price reversals.
    
    Arguments:
    - ticker (str): The ticker symbol.
    
    Keywords: liquidity, trading activity, turnover, share volume, market interest.
    """
    from mcp_servers.yfinance_server.tools import market
    return await market.get_volume(ticker)

@mcp.tool()
async def get_beta(ticker: str) -> str:
    """FETCHES Beta volatility. [ACTION]
    
    [RAG Context]
    Beta is a measure of a stock's volatility in relation to the overall market (usually the S&P 500).
    
    Interpretation:
    - Beta = 1.0: Stock moves with the market.
    - Beta > 1.0: More volatile than the market (High Beta). Good for aggressive growth strategies.
    - Beta < 1.0: Less volatile than the market (Low Beta). Good for defensive or conservative portfolios.
    - Beta = 0: No correlation with the market (e.g., cash).
    
    How to Use:
    - Use this to assess the risk level of an individual asset within a diversified portfolio.
    
    Arguments:
    - ticker (str): The ticker symbol.
    
    Keywords: risk, volatility, market correlation, systemic risk, CAPM.
    """
    from mcp_servers.yfinance_server.tools import market
    return await market.get_beta(ticker)

@mcp.tool()
async def get_quote_metadata(ticker: str) -> str:
    """FETCHES quote metadata. [ACTION]
    
    [RAG Context]
    Returns detailed technical metadata about the current quote from the exchange.
    
    Included Fields:
    - Bid/Ask prices and sizes: The prices at which buyers are willing to buy and sellers are willing to sell.
    - Currency: The currency in which the asset is traded (e.g., USD, EUR, IDR).
    - Exchange Name: The primary exchange where the ticker is listed (e.g., NASDAQ, NYSE, JSX).
    - Timezone: The timezone of the exchange, critical for knowing if the market is open.
    
    How to Use:
    - Use this for high-precision algorithmic checks or when currency conversion is needed for international stocks.
    
    Arguments:
    - ticker (str): The ticker symbol.
    
    Keywords: bid-ask spread, currency, exchange info, trading hours, raw quote.
    """
    from mcp_servers.yfinance_server.tools import market
    return await market.get_quote_metadata(ticker)

@mcp.tool()
async def get_bulk_historical_data(tickers: str = None, ticker: str = None, period: str = "1mo", interval: str = "1d") -> str:
    """FETCHES historical data (Bulk). [ACTION]
    
    [RAG Context]
    Downloads historical price and volume data for one or more tickers over a specified timeframe. This is the primary tool for trend analysis and technical modeling.
    
    How to Use:
    - Provide a string of space-separated tickers: "AAPL MSFT GOOGL".
    - Period: Defines how far back to go. Options: "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max".
    - Interval: Defines the data density. Options: "1m" (intraday, limited to last 7 days), "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo".
    - Result: Returns a CSV-formatted string with Open, High, Low, Close, and Volume columns.
    
    Arguments:
    - tickers: Space-separated symbols string.
    - ticker: Alias for tickers if requesting only one.
    - period: Standard yfinance time periods.
    - interval: Data frequency.
    
    Example:
    - Input: tickers="AAPL MSFT", period="1mo", interval="1d"
    
    Keywords: OHLC, price history, bulk download, time series, market trends.
    """
    from mcp_servers.yfinance_server.tools import market
    return await market.get_bulk_historical_data(tickers, ticker, period, interval)

# --- Financials ---
@mcp.tool()
async def get_income_statement_annual(ticker: str) -> str:
    """FETCHES Annual Income Statement. [ACTION]
    
    [RAG Context]
    Provides the standardized annual income statement for the last 4 fiscal years. 
    It details a company's financial performance over a reporting period, specifically its revenues, expenses, and profits/losses.
    
    Key Metrics to observe:
    - Total Revenue (Top line growth).
    - Gross Profit (Efficiency of production).
    - EBITDA (Operational profitability).
    - Net Income (Bottom line / real profit).
    
    How to Use:
    - Use for fundamental "Deep Dive" analysis to verify if a company is actually making money or just growing revenue.
    
    Arguments:
    - ticker (str): The ticker symbol.
    
    Keywords: P&L, profit and loss, revenue, net income, margins, financial health.
    """
    from mcp_servers.yfinance_server.tools import financials
    return await financials.get_income_statement_annual(ticker)

@mcp.tool()
async def get_income_statement_quarterly(ticker: str) -> str:
    """FETCHES Quarterly Income Statement. [ACTION]
    
    [RAG Context]
    Provides the income statement for the last 4 fiscal quarters.
    
    How to Use:
    - Crucial for identifying recent momentum changes or seasonal trends (e.g., retail stocks peaking in Q4).
    - Check for "Earnings Surprises" by comparing these values to past estimates.
    
    Arguments:
    - ticker (str): The ticker symbol.
    
    Keywords: quarterly earnings, short-term performance, recent revenue, seasonal analysis.
    """
    from mcp_servers.yfinance_server.tools import financials
    return await financials.get_income_statement_quarterly(ticker)

@mcp.tool()
async def get_balance_sheet_annual(ticker: str) -> str:
    """FETCHES Annual Balance Sheet. [ACTION]
    
    [RAG Context]
    Retrieves the annual balance sheet, showing what a company owns (Assets) and what it owes (Liabilities) at the end of the fiscal year.
    
    Key Data Points:
    - Total Assets vs Total Liabilities.
    - Cash and Equivalents (Liquidity).
    - Total Debt (Solvency risk).
    - Stockholders Equity (Net value).
    
    How to Use:
    - Use to calculate debt-to-equity ratios and evaluate long-term financial stability.
    
    Arguments:
    - ticker (str): The ticker symbol.
    
    Keywords: assets, liabilities, debt, equity, solvency, book value.
    """
    from mcp_servers.yfinance_server.tools import financials
    return await financials.get_balance_sheet_annual(ticker)

@mcp.tool()
async def get_balance_sheet_quarterly(ticker: str) -> str:
    """FETCHES Quarterly Balance Sheet. [ACTION]
    
    [RAG Context]
    Retrieves the most recent quarterly balance sheet updates.
    
    How to Use:
    - Identify rapid changes in debt levels or cash burn between annual reports.
    - Essential for distressed company analysis or fast-moving tech stocks.
    
    Arguments:
    - ticker (str): The ticker symbol.
    
    Keywords: current assets, current liabilities, working capital, debt ratios.
    """
    from mcp_servers.yfinance_server.tools import financials
    return await financials.get_balance_sheet_quarterly(ticker)

@mcp.tool()
async def get_cash_flow_statement_annual(ticker: str) -> str:
    """FETCHES Annual Cash Flow. [ACTION]
    
    [RAG Context]
    Provides the annual statement of cash flows, which tracks the actual movement of cash in and out of the business.
    
    Sections included:
    - Operating Cash Flow (Cash from core business).
    - Investing Cash Flow (Cash spent on CapEx/Acquisitions).
    - Financing Cash Flow (Cash from debt/dividends/buybacks).
    
    Free Cash Flow (FCF) Calculation:
    - Subtract Capital Expenditures from Operating Cash Flow.
    
    How to Use:
    - Essential because "Earnings" can be manipulated via accounting, but "Cash Flow" is harder to fake.
    
    Arguments:
    - ticker (str): The ticker symbol.
    
    Keywords: cash flow, FCF, CapEx, operating cash, financing activities.
    """
    from mcp_servers.yfinance_server.tools import financials
    return await financials.get_cash_flow_statement_annual(ticker)

@mcp.tool()
async def get_cash_flow_statement_quarterly(ticker: str) -> str:
    """FETCHES Quarterly Cash Flow. [ACTION]
    
    [RAG Context]
    Recent quarterly cash movement patterns.
    
    How to Use:
    - Use to detect "Cash Burn" in startups or changes in dividend sustainability.
    
    Arguments:
    - ticker (str): The ticker symbol.
    
    Keywords: quarterly cash, burn rate, liquidity flow.
    """
    from mcp_servers.yfinance_server.tools import financials
    return await financials.get_cash_flow_statement_quarterly(ticker)

# --- Holders ---
@mcp.tool()
async def get_major_holders(ticker: str) -> str:
    """FETCHES major holders breakdown. [ACTION]
    
    [RAG Context]
    Returns the percentage breakdown of ownership between Insiders, Institutions, and the Public Float.
    
    Interpretation:
    - High Institutional Ownership: Indicates "Smart Money" support and stability.
    - High Insider Ownership: Suggests management's interests are aligned with shareholders (they "eat their own cooking").
    
    How to Use:
    - Use to verify the "conviction" behind a stock.
    
    Arguments:
    - ticker (str): The ticker symbol.
    
    Keywords: ownership, insiders, institutions, float, who owns the stock.
    """
    from mcp_servers.yfinance_server.tools import holders
    return await holders.get_major_holders_breakdown(ticker)

@mcp.tool()
async def get_institutional_holders(ticker: str) -> str:
    """FETCHES institutional holders. [ACTION]
    
    [RAG Context]
    Lists the top institutional investors and their share counts. 
    Examples of institutions: BlackRock, Vanguard, State Street, Berkshire Hathaway.
    
    How to Use:
    - Check if the "Who's Who" of Wall Street is buying or selling the stock.
    
    Arguments:
    - ticker (str): The ticker symbol.
    
    Keywords: big banks, hedge funds, asset managers, institutional investors.
    """
    from mcp_servers.yfinance_server.tools import holders
    return await holders.get_institutional_holders(ticker)

@mcp.tool()
async def get_mutual_funds(ticker: str) -> str:
    """FETCHES mutual fund holders. [ACTION]
    
    [RAG Context]
    Lists the top mutual funds that hold the stock.
    
    How to Use:
    - Understand which indexes or thematic funds include this stock.
    
    Arguments:
    - ticker (str): The ticker symbol.
    
    Keywords: ETFs, mutual funds, passive investors, index funds.
    """
    from mcp_servers.yfinance_server.tools import holders
    return await holders.get_mutual_fund_holders(ticker)

@mcp.tool()
async def get_insider_transactions(ticker: str) -> str:
    """FETCHES insider transactions. [ACTION]
    
    [RAG Context]
    Tracks recent buy and sell transactions by company executives and directors (form 4 filings).
    
    Signal Strength:
    - Insider Buying: VERY BULLISH signal.
    - Insider Selling: Can be bearish, but often just for tax planning or diversification.
    
    How to Use:
    - Monitor if the CEO/CFO is putting their own money into the stock.
    
    Arguments:
    - ticker (str): The ticker symbol.
    
    Keywords: insider trading, CEO buying, management transactions, form 4.
    """
    from mcp_servers.yfinance_server.tools import holders
    return await holders.get_insider_transactions(ticker)

@mcp.tool()
async def get_insider_roster(ticker: str) -> str:
    """FETCHES insider roster. [ACTION]
    
    [RAG Context]
    Provides the names, positions, and shareholdings of the company's key executives and board members.
    
    How to Use:
    - Identify the leadership team.
    
    Arguments:
    - ticker (str): The ticker symbol.
    
    Keywords: board of directors, executives, management team, insiders.
    """
    from mcp_servers.yfinance_server.tools import holders
    return await holders.get_insider_roster(ticker)

# --- Analysis ---
@mcp.tool()
async def get_analyst_ratings(ticker: str) -> str:
    """FETCHES analyst ratings. [ACTION]
    
    [RAG Context]
    Returns the consensus recommendation from Wall Street analysts. 
    Ratings typically range from "Strong Buy", "Buy", "Hold", "Sell" to "Strong Sell".
    
    How to Use:
    - Use this to gauge broader market sentiment and expectation.
    - Be cautious: analyst ratings are often lagging indicators.
    
    Arguments:
    - ticker (str): The ticker symbol.
    
    Keywords: buy sell hold, analyst consensus, recommendations, sentiment.
    """
    from mcp_servers.yfinance_server.tools import analysis
    return await analysis.get_analyst_recommendations(ticker)

@mcp.tool()
async def get_price_targets(ticker: str) -> str:
    """FETCHES price targets. [ACTION]
    
    [RAG Context]
    Returns the average, high, and low 12-month price targets set by research analysts.
    
    How to Use:
    - Compare the current price to the "Mean Target" to see the "Implied Upside" or "Downside".
    
    Arguments:
    - ticker (str): The ticker symbol.
    
    Keywords: price prediction, target price, upside potential, valuation targets.
    """
    from mcp_servers.yfinance_server.tools import analysis
    return await analysis.get_price_targets(ticker)

@mcp.tool()
async def get_upgrades_downgrades(ticker: str) -> str:
    """FETCHES upgrades/downgrades. [ACTION]
    
    [RAG Context]
    Lists the most recent rating changes from specific investment banks (e.g., Goldman Sachs, JP Morgan).
    
    How to Use:
    - "Upgrades" usually catalyze immediate price increases.
    - "Downgrades" often trigger sell-offs.
    
    Arguments:
    - ticker (str): The ticker symbol.
    
    Keywords: analyst changes, rating updates, bank ratings.
    """
    from mcp_servers.yfinance_server.tools import analysis
    return await analysis.get_upgrades_downgrades(ticker)

@mcp.tool()
async def get_earnings_calendar(ticker: str) -> str:
    """FETCHES earnings calendar. [ACTION]
    
    [RAG Context]
    Returns the date of the next earnings announcement and the current EPS (Earnings Per Share) estimates.
    
    How to Use:
    - Mark these dates! Earnings calls are high-volatility events where stock prices can jump 10-20% in minutes.
    
    Arguments:
    - ticker (str): The ticker symbol.
    
    Keywords: earnings date, next call, EPS estimate, fiscal release.
    """
    from mcp_servers.yfinance_server.tools import analysis
    return await analysis.get_earnings_calendar(ticker)

@mcp.tool()
async def get_dividends_history(ticker: str) -> str:
    """FETCHES dividend history. [ACTION]
    
    [RAG Context]
    Returns a historical record of all dividend payments made by the company.
    
    How to Use:
    - Use this to calculate Dividend Yield, Dividend Growth Rate, and payment consistency.
    - Essential for "Income Investing" or "Dividend Aristocrat" research.
    
    Arguments:
    - ticker (str): The ticker symbol.
    
    Keywords: dividends, yields, passive income, payout history.
    """
    from mcp_servers.yfinance_server.tools import analysis
    return await analysis.get_dividends_history(ticker)

@mcp.tool()
async def get_splits_history(ticker: str) -> str:
    """FETCHES split history. [ACTION]
    
    [RAG Context]
    Lists historical stock splits (e.g., 2-for-1, 7-for-1).
    
    How to Use:
    - Splits make shares more affordable for retail investors but don't change the underlying company value.
    
    Arguments:
    - ticker (str): The ticker symbol.
    
    Keywords: stock splits, reverse splits, share adjustment.
    """
    from mcp_servers.yfinance_server.tools import analysis
    return await analysis.get_splits_history(ticker)

@mcp.tool()
async def calculate_indicators(ticker: str, indicators: List[str] = ["sma", "rsi"], period: str = "1y", interval: str = "1d") -> str:
    """CALCULATES technical indicators. [ACTION]
    
    [RAG Context]
    Performs algorithmic calculations on historical price data to derive technical indicators.
    
    Available Indicators:
    - sma (Simple Moving Average): Identifies trend direction.
    - ema (Exponential Moving Average): Places more weight on recent prices.
    - rsi (Relative Strength Index): Measures overbought (>70) or oversold (<30) conditions.
    - macd (Moving Average Convergence Divergence): Momentum indicator.
    - bbands (Bollinger Bands): Measures volatility and price extremes.
    
    How to Use:
    - Use this for "Technical Analysis" or to identify "Entry/Exit Points" for trades.
    
    Arguments:
    - ticker: The stock symbol.
    - indicators: A list of strings representing the desired indicators.
    - period/interval: Same as historical data settings.
    
    Keywords: technical analysis, momentum, overbought, oversold, charting metrics.
    """
    from mcp_servers.yfinance_server.tools import analysis
    return await analysis.calculate_indicators(ticker, indicators, period=period, interval=interval)

# --- Charts ---
@mcp.tool()
async def get_price_chart(ticker: str, period: str = "1y") -> Image:
    """GENERATES price chart. [ACTION]
    
    [RAG Context]
    Creates a visual representation of price performance over time.
    
    How to Use:
    - Returns an 'Image' object (PNG format) that can be displayed to the user.
    - Period options: "1d", "5d", "1mo", "6mo", "1y", "5y", "max".
    
    Arguments:
    - ticker: The stock symbol.
    - period: The timeframe for the x-axis.
    
    Keywords: visualization, plotting, line chart, price visual, technical chart.
    """
    from mcp_servers.yfinance_server.tools import charts
    return await charts.get_price_chart(ticker, period)

# --- Options ---
@mcp.tool()
async def get_options_chain(ticker: str, date: str = "", limit: int = 10) -> str:
    """FETCHES options chain (Calls/Puts). [ACTION]
    
    [RAG Context]
    Retrieves the table of available option contracts for a specific expiration date.
    
    How to Use:
    - Returns Strike Price, Last Price, Change, % Change, Volume, and Open Interest.
    - Essential for hedging or speculative options strategies.
    
    Arguments:
    - ticker: The symbol.
    - date: The 'YYYY-MM-DD' expiration (must be a valid Friday, use 'get_option_expirations' first).
    - limit: Max rows to return to prevent character limit issues.
    
    Keywords: calls, puts, strikes, hedging, derivatives, leverage.
    """
    from mcp_servers.yfinance_server.tools import options
    return await options.get_options_chain(ticker, date, limit=limit)

@mcp.tool()
async def get_option_expirations(ticker: str) -> str:
    """FETCHES option expirations. [ACTION]
    
    [RAG Context]
    Returns a list of all future dates on which options contracts for this ticker will expire.
    
    How to Use:
    - You MUST call this before calling 'get_options_chain' to ensure the date you provide is valid.
    
    Arguments:
    - ticker: The symbol.
    
    Keywords: expiration dates, option monthlys, weeklys.
    """
    from mcp_servers.yfinance_server.tools import options
    return await options.get_option_expirations(ticker)

# --- Aggregators ---
@mcp.tool()
async def get_tickers_by_country(country_code: str, limit: int = 50) -> str:
    """SEARCHES tickers by country. [ACTION]
    
    [RAG Context]
    Allows for broad discovery of companies listed in specific geographic regions.
    
    How to Use:
    - Use standard 2-letter ISO country codes (e.g., "US", "ID", "GB", "JP").
    - Useful for Top-Down macroeconomic analysis or international diversification.
    
    Arguments:
    - country_code: ISO 3166-1 alpha-2 code.
    - limit: Sample size.
    
    Keywords: discover stocks, country list, international equities, regional screening.
    """
    from mcp_servers.yfinance_server.tools import discovery
    return await discovery.get_tickers_by_country(country_code, limit=limit)

@mcp.tool()
async def get_full_report(ticker: str) -> str:
    """GENERATES full financial report. [ACTION]
    
    [RAG Context]
    This is a "Super Tool" that aggregates data from Profile, Price, Income Statement, Balance Sheet, Cash Flow, and Holders into one comprehensive text block.
    
    How to Use:
    - Use this tool when the user asks for a "Deep Dive", "Full Analysis", or "Tell me everything about X".
    - It significantly reduces the number of tool calls and provides a holistic view of the company in one turn.
    
    Arguments:
    - ticker: The symbol.
    
    Keywords: comprehensive research, company overview, due diligence, all-in-one report.
    """
    from mcp_servers.yfinance_server.tools import aggregators
    return await aggregators.get_full_ticker_report(ticker)

# --- Dynamic Info Tool ---
@mcp.tool()
async def get_ticker_info(ticker: str, key: str = "longName") -> str:
    """EXTRACTS raw metric from info. [ACTION]
    
    [RAG Context]
    Provides direct access to'yfinance''s internal 'info' dictionary for specific keys that may not have dedicated tools.
    
    Available Keys Include:
    - auditRisk, boardRisk, compensationRisk (Governance)
    - priceToBook, pegRatio, forwardPE (Valuation)
    - debtToEquity, quickRatio, currentRatio (Liquidity)
    - returnOnEquity, returnOnAssets (Profitability)
    - totalRevenue, revenueGrowth (Growth)
    - floatShares, shortRatio, shortPercentOfFloat (Technicals)
    
    How to Use:
    - Pass the exact key name to extract just that value.
    
    Arguments:
    - ticker: The symbol.
    - key: The metric key string.
    
    Keywords: direct access, raw data, advanced metrics, info dict.
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

