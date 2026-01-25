
from yahooquery import search
from mcp_servers.yahooquery_server.tools.ticker import SmartTicker
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
import pandas as pd
import json

logger = get_logger(__name__)

# --- FUNDS ENGINE ---

async def get_fund_holdings_formatted(arguments: dict) -> ToolResult:
    """
    Get Table of Top Holdings for ETFs/Mutual Funds.
    """
    tickers = arguments.get("tickers")
    try:
        st = SmartTicker(tickers)
        # fundHoldingInfo usually contains cashPosition, stockPosition, bondPosition
        # fundTopHoldings contains the rows
        
        data = st.yq.fund_top_holdings
        if isinstance(data, pd.DataFrame):
            return ToolResult(content=[TextContent(text=f"### Top Holdings\n\n{data.to_markdown()}")])
        
        # If dict (multi-ticker or weird format)
        return ToolResult(content=[TextContent(text=json.dumps(data, indent=2, default=str))])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_fund_sector_weightings(arguments: dict) -> ToolResult:
    """Get Sector Weightings for Funds."""
    tickers = arguments.get("tickers")
    try:
        st = SmartTicker(tickers)
        data = st.yq.fund_sector_weightings
        if isinstance(data, pd.DataFrame):
             return ToolResult(content=[TextContent(text=f"### Sector Weightings\n\n{data.to_markdown()}")])
        return ToolResult(content=[TextContent(text=json.dumps(data, indent=2, default=str))])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

# --- DISCOVERY ENGINE ---

async def search_instruments(arguments: dict) -> ToolResult:
    """
    Search for ANY financial instrument (Stocks, Forex, Crypto, Bonds).
    Args:
        query (str): "Gold", "Bitcoin", "Vanguard", "EURUSD"
    """
    q = arguments.get("query")
    try:
        # yahooquery.search returns dict: {'quotes': [...], 'news': [...]}
        data = search(q)
        if "quotes" in data:
            quotes = data["quotes"]
            # Simplify
            simple = [{k: x.get(k) for k in ["symbol", "shortname", "longname", "score", "quoteType", "exchange"]} for x in quotes]
            return ToolResult(content=[TextContent(text=f"### Search Results: '{q}'\n\n" + pd.DataFrame(simple).to_markdown())])
            
        return ToolResult(content=[TextContent(text=json.dumps(data, indent=2))])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_ticker_news(arguments: dict) -> ToolResult:
    """Get News for specific tickers."""
    tickers = arguments.get("tickers")
    try:
        # news is a property of Ticker
        st = SmartTicker(tickers)
        data = st.yq.news
        return ToolResult(content=[TextContent(text=json.dumps(data, indent=2))])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
