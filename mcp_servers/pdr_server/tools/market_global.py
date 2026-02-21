
import pandas_datareader.data as web

from shared.logging.main import get_logger
import pandas as pd
import datetime

logger = get_logger(__name__)


async def get_stooq_data(symbols: list[str], start_date: str = None) -> str:
    """
    Get Stooq Data (Indices, Macro, ETFs).
    Useful for: US Bonds (US10Y.B), Currencies, Commodities.
    """
    # symbols = arguments.get("symbols") # List of symbols
    # start_date = arguments.get("start_date")
    
    if not start_date:
        start = datetime.datetime.now() - datetime.timedelta(days=365)
    else:
        start = start_date
        
    try:
        end = datetime.datetime.now()
        # Returns DataFrame with MultiIndex columns if multiple symbols
        df = web.DataReader(symbols, "stooq", start=start, end=end)

        # Clean NaT values which crash to_markdown/strftime
        df.index = pd.to_datetime(df.index, errors='coerce')
        if isinstance(df.index, pd.DatetimeIndex):
            df = df[df.index.notna()]

        return f"### Stooq Data (Last 50 rows)\n\n{df.head(50).to_markdown()}"
        
    except Exception as e:
        logger.error(f"Stooq error {symbols}: {e}")
        return f"Error: {str(e)}"

async def get_tsp_fund_data() -> str:
    """
    Get Thrift Savings Plan (TSP) Fund Data.
    """
    try:
        start = datetime.datetime.now() - datetime.timedelta(days=365)
        df = web.DataReader("TSP", "tsp", start=start)
        
        return f"### TSP Funds (Last 50 days)\n\n{df.tail(50).to_markdown()}"
    except Exception as e:
        return f"Error: {str(e)}"

async def get_moex_data(symbols: list[str], start_date: str = None) -> str:
    """
    Get Moscow Exchange (MOEX) Data.
    Unlocks Russian market data.
    """
    # symbols = arguments.get("symbols")
    # start_date = arguments.get("start_date")
    
    if not start_date:
        start = datetime.datetime.now() - datetime.timedelta(days=365)
    else:
        start = start_date
        
    try:
        # PDR source 'moex'
        df = web.DataReader(symbols, "moex", start=start)
        return f"### MOEX Data\n\n{df.tail(50).to_markdown()}"
    except Exception as e:
        return f"Error: {str(e)}"

