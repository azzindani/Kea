
import ccxt.async_support as ccxt

import ccxt.async_support as ccxt
from shared.logging import get_logger
import pandas as pd
from mcp_servers.ccxt_server.tools.exchange_manager import get_exchange_instance

logger = get_logger(__name__)


# --- PUBLIC TOOLS ---

async def get_ticker(exchange: str = "binance", symbol: str = "BTC/USDT") -> str:
    """
    Get Ticker for a Symbol (Unified).
    """
    try:
        ex = await get_exchange_instance(exchange)
        ticker = await ex.fetch_ticker(symbol)
        
        # Flatten for display
        df = pd.DataFrame([ticker])
        cols = ['symbol', 'last', 'bid', 'ask', 'high', 'low', 'baseVolume', 'quoteVolume', 'percentage', 'datetime']
        cols = [c for c in cols if c in df.columns]
        
        return f"### Ticker: {symbol} on {exchange}\n\n{df[cols].to_markdown()}"
    except Exception as e:
        return f"Error: {str(e)}"

async def get_ohlcv(exchange: str = "binance", symbol: str = "BTC/USDT", timeframe: str = "1d", limit: int = 100000) -> str:
    """
    Get OHLCV (Candles).
    """
    try:
        ex = await get_exchange_instance(exchange)
        if ex.has['fetchOHLCV']:
            ohlcv = await ex.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return f"### OHLCV: {symbol} ({timeframe})\n\n{df.tail(limit).to_markdown()}"
        else:
             return f"{exchange} does not support fetchOHLCV."
    except Exception as e:
        return f"Error: {str(e)}"

async def get_order_book(exchange: str = "binance", symbol: str = "BTC/USDT", limit: int = 100000) -> str:
    """
    Get Order Book (Depth).
    """
    try:
        ex = await get_exchange_instance(exchange)
        book = await ex.fetch_order_book(symbol, limit)
        
        # Format Bids/Asks
        bids = pd.DataFrame(book['bids'], columns=['price', 'amount']).head(limit)
        asks = pd.DataFrame(book['asks'], columns=['price', 'amount']).head(limit)
        
        output = f"### Order Book: {symbol} (Top {limit})\n\n**Bids (Buy)**\n{bids.to_markdown()}\n\n**Asks (Sell)**\n{asks.to_markdown()}"
        return output
    except Exception as e:
        return f"Error: {str(e)}"

async def get_trades(exchange: str = "binance", symbol: str = "BTC/USDT", limit: int = 100000) -> str:
    """
    Get Recent Trades (Executions).
    """
    try:
        ex = await get_exchange_instance(exchange)
        trades = await ex.fetch_trades(symbol, limit=limit)
        df = pd.DataFrame(trades)
        
        cols = ['timestamp', 'datetime', 'symbol', 'side', 'price', 'amount', 'cost']
        cols = [c for c in cols if c in df.columns]
        
        return f"### Recent Trades: {symbol}\n\n{df[cols].tail(limit).to_markdown()}"
    except Exception as e:
         return f"Error: {str(e)}"

async def get_status(exchange: str = "binance") -> str:
    """
    Get Exchange Status (Health).
    """
    try:
        ex = await get_exchange_instance(exchange)
        status = await ex.fetch_status()
        return f"### Status: {exchange}\n\n{status}"
    except Exception as e:
         return f"Error: {str(e)}"

async def get_time(exchange: str = "binance") -> str:
    """
    Get Exchange Server Time.
    """
    try:
        ex = await get_exchange_instance(exchange)
        time = await ex.fetch_time()
        # Convert to ISO
        import datetime
        dt = datetime.datetime.fromtimestamp(time/1000)
        return f"### Time: {exchange}\nTimestamp: {time}\nISO: {dt}"
    except Exception as e:
         return f"Error: {str(e)}"

