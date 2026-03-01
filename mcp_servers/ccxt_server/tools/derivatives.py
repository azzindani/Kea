
import ccxt.async_support as ccxt
import ccxt.async_support as ccxt
from shared.logging.main import get_logger
from mcp_servers.ccxt_server.tools.exchange_manager import get_exchange_instance
import pandas as pd

logger = get_logger(__name__)


# --- DERIVATIVES ---

async def get_funding_rate(exchange: str = "binance", symbol: str = "BTC/USDT") -> str:
    """
    Get Funding Rate (Futures/Perps).
    """
    try:
        ex = await get_exchange_instance(exchange)
        if hasattr(ex, 'fetchFundingRate'):
            rate = await ex.fetch_funding_rate(symbol)
            # Flatten
            # usually has: fundingRate, timestamp, nextFundingTime
            df = pd.DataFrame([rate])
            cols = ['symbol', 'fundingRate', 'timestamp', 'datetime', 'nextFundingTime', 'nextFundingRate']
            cols = [c for c in cols if c in df.columns]
            return f"### Funding Rate: {symbol} on {exchange}\n\n{df[cols].to_markdown()}"
        else:
            return f"{exchange} does not support fetchFundingRate."
    except Exception as e:
        return f"Error: {str(e)}"

async def get_open_interest(exchange: str = "binance", symbol: str = "BTC/USDT") -> str:
    """
    Get Open Interest (Futures/Perps).
    """
    try:
        ex = await get_exchange_instance(exchange)
        if hasattr(ex, 'fetchOpenInterest'):
            oi = await ex.fetch_open_interest(symbol)
            # oi keys: symbol, openInterestAmount, openInterestValue, timestamp
            df = pd.DataFrame([oi])
            return f"### Open Interest: {symbol}\n\n{df.to_markdown()}"
        else:
             return f"{exchange} does not support fetchOpenInterest."
    except Exception as e:
        return f"Error: {str(e)}"

