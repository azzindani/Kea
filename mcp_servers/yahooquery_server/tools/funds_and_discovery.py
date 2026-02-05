
from yahooquery import search
from mcp_servers.yahooquery_server.tools.ticker import SmartTicker
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
import pandas as pd
import json

logger = get_logger(__name__)


# --- FUNDS ENGINE ---

async def get_fund_holdings_formatted(tickers: str) -> str:
    """
    Get Table of Top Holdings for ETFs/Mutual Funds.
    """
    try:
        st = SmartTicker(tickers)
        # fundHoldingInfo usually contains cashPosition, stockPosition, bondPosition
        # fundTopHoldings contains the rows
        
        data = st.yq.fund_top_holdings
        if isinstance(data, pd.DataFrame):
            return f"### Top Holdings\n\n{data.to_markdown()}"
        
        # If dict (multi-ticker or weird format)
        return json.dumps(data, indent=2, default=str)
    except Exception as e:
        return f"Error: {str(e)}"

async def get_fund_sector_weightings(tickers: str) -> str:
    """Get Sector Weightings for Funds."""
    try:
        st = SmartTicker(tickers)
        data = st.yq.fund_sector_weightings
        if isinstance(data, pd.DataFrame):
             return f"### Sector Weightings\n\n{data.to_markdown()}"
        return json.dumps(data, indent=2, default=str)
    except Exception as e:
        return f"Error: {str(e)}"

# --- DISCOVERY ENGINE ---

async def search_instruments(query: str) -> str:
    """
    Search for ANY financial instrument (Stocks, Forex, Crypto, Bonds).
    Args:
        query (str): "Gold", "Bitcoin", "Vanguard", "EURUSD"
    """
    
    try:
        # yahooquery.search returns dict: {'quotes': [...], 'news': [...]}
        data = search(query)
        if "quotes" in data:
            quotes = data["quotes"]
            # Simplify
            simple = [{k: x.get(k) for k in ["symbol", "shortname", "longname", "score", "quoteType", "exchange"]} for x in quotes]
            return f"### Search Results: '{query}'\n\n" + pd.DataFrame(simple).to_markdown()
            
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

async def get_ticker_news(tickers: str) -> str:
    """Get News for specific tickers."""
    try:
        # news is a property of Ticker
        st = SmartTicker(tickers)
        data = st.yq.news
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"

