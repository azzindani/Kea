
import ccxt.async_support as ccxt
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
import pandas as pd
from mcp_servers.ccxt_server.tools.exchange_manager import get_exchange_instance

logger = get_logger(__name__)

async def get_ticker(arguments: dict) -> ToolResult:
    """
    Get Ticker for a Symbol (Unified).
    """
    exchange_id = arguments.get("exchange", "binance")
    symbol = arguments.get("symbol") # e.g. "BTC/USDT"
    
    try:
        exchange = await get_exchange_instance(exchange_id)
        ticker = await exchange.fetch_ticker(symbol)
        
        # Flatten for display
        # Ticker has: high, low, bid, ask, last, volume, etc.
        # Let's format nicely
        df = pd.DataFrame([ticker])
        # Select key columns if possible, or show all
        cols = ['symbol', 'last', 'bid', 'ask', 'high', 'low', 'baseVolume', 'quoteVolume', 'percentage', 'datetime']
        # Filter existing cols
        cols = [c for c in cols if c in df.columns]
        
        return ToolResult(content=[TextContent(text=f"### Ticker: {symbol} on {exchange_id}\n\n{df[cols].to_markdown()}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_ohlcv(arguments: dict) -> ToolResult:
    """
    Get OHLCV (Candles).
    """
    exchange_id = arguments.get("exchange", "binance")
    symbol = arguments.get("symbol")
    timeframe = arguments.get("timeframe", "1d")
    limit = arguments.get("limit", 100)
    
    try:
        exchange = await get_exchange_instance(exchange_id)
        if exchange.has['fetchOHLCV']:
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return ToolResult(content=[TextContent(text=f"### OHLCV: {symbol} ({timeframe})\n\n{df.tail(limit).to_markdown()}")])
        else:
             return ToolResult(content=[TextContent(text=f"{exchange_id} does not support fetchOHLCV.")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_order_book(arguments: dict) -> ToolResult:
    """
    Get Order Book (Depth).
    """
    exchange_id = arguments.get("exchange", "binance")
    symbol = arguments.get("symbol")
    limit = arguments.get("limit", 10)
    
    try:
        exchange = await get_exchange_instance(exchange_id)
        book = await exchange.fetch_order_book(symbol, limit)
        
        # Format Bids/Asks
        bids = pd.DataFrame(book['bids'], columns=['price', 'amount']).head(limit)
        asks = pd.DataFrame(book['asks'], columns=['price', 'amount']).head(limit)
        
        output = f"### Order Book: {symbol} (Top {limit})\n\n**Bids (Buy)**\n{bids.to_markdown()}\n\n**Asks (Sell)**\n{asks.to_markdown()}"
        return ToolResult(content=[TextContent(text=output)])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_trades(arguments: dict) -> ToolResult:
    """
    Get Recent Trades (Executions).
    """
    exchange_id = arguments.get("exchange", "binance")
    symbol = arguments.get("symbol")
    limit = arguments.get("limit", 20)
    
    try:
        exchange = await get_exchange_instance(exchange_id)
        trades = await exchange.fetch_trades(symbol, limit=limit)
        df = pd.DataFrame(trades)
        
        # Select useful cols
        cols = ['timestamp', 'datetime', 'symbol', 'side', 'price', 'amount', 'cost']
        cols = [c for c in cols if c in df.columns]
        
        return ToolResult(content=[TextContent(text=f"### Recent Trades: {symbol}\n\n{df[cols].tail(limit).to_markdown()}")])
    except Exception as e:
         return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_status(arguments: dict) -> ToolResult:
    """
    Get Exchange Status (Health).
    """
    exchange_id = arguments.get("exchange", "binance")
    try:
        exchange = await get_exchange_instance(exchange_id)
        status = await exchange.fetch_status()
        return ToolResult(content=[TextContent(text=f"### Status: {exchange_id}\n\n{status}")])
    except Exception as e:
         return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_time(arguments: dict) -> ToolResult:
    """
    Get Exchange Server Time.
    """
    exchange_id = arguments.get("exchange", "binance")
    try:
        exchange = await get_exchange_instance(exchange_id)
        time = await exchange.fetch_time()
        # Convert to ISO
        import datetime
        dt = datetime.datetime.fromtimestamp(time/1000)
        return ToolResult(content=[TextContent(text=f"### Time: {exchange_id}\nTimestamp: {time}\nISO: {dt}")])
    except Exception as e:
         return ToolResult(isError=True, content=[TextContent(text=str(e))])
