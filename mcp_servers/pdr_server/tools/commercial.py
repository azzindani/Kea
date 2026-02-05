
import pandas_datareader.data as web

from shared.logging import get_logger
import datetime
import os

logger = get_logger(__name__)


async def get_tiingo_data(symbols: list[str] = None, api_key: str = None, start_date: str = None) -> str:
    """
    Get Tiingo Stock/ETF Data (Requires API Key).
    Set TIINGO_API_KEY env var or pass key.
    """
    key = api_key or os.getenv("TIINGO_API_KEY")
    
    if not key:
        return "Error: Tiingo API Key required. Set TIINGO_API_KEY environment variable or pass 'api_key'."
        
    if not start_date:
        start = datetime.datetime.now() - datetime.timedelta(days=365)
    else:
        start = start_date
        
    try:
        # Tiingo returns multi-index or single depending on symbols
        df = web.DataReader(symbols, "tiingo", start=start, api_key=key)
        
        return f"### Tiingo Data\n\n{df.tail(50).to_markdown()}"
    except Exception as e:
        return f"Error: {str(e)}"

async def get_alphavantage_data(symbols: list[str] = None, api_key: str = None, start_date: str = None) -> str:
    """
    Get AlphaVantage Stock Data (Requires API Key).
    Set ALPHAVANTAGE_API_KEY env var or pass key.
    """
    key = api_key or os.getenv("ALPHAVANTAGE_API_KEY")
    
    # PDR uses "av-daily" or "av-forex" etc. 
    # 'av-daily' gets daily time series.
    
    if not key:
        return "Error: AlphaVantage API Key required."
        
    if not start_date:
        start = datetime.datetime.now() - datetime.timedelta(days=365)
    else:
        start = start_date
        
    try:
        # PDR supports 'av-daily', 'av-daily-adjusted'
        # symbols argument here is meant to be a single string for AV?
        # Let's try iterating if list.
        if isinstance(symbols, list):
            symbol = symbols[0]
        else:
            symbol = symbols
            
        df = web.DataReader(symbol, "av-daily", start=start, api_key=key)
        return f"### AlphaVantage ({symbol})\n\n{df.tail(50).to_markdown()}"
    except Exception as e:
        return f"Error: {str(e)}"

