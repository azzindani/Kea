
import ccxt.async_support as ccxt
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
from mcp_servers.ccxt_server.tools.exchange_manager import get_exchange_instance
import pandas as pd
import asyncio

logger = get_logger(__name__)

async def download_history(arguments: dict) -> ToolResult:
    """
    Download Historical OHLCV (Pagination).
    Fetches MORE than exchange limit by looping.
    """
    exchange_id = arguments.get("exchange", "binance")
    symbol = arguments.get("symbol")
    timeframe = arguments.get("timeframe", "1h")
    # 'days' back or 'limit'
    days = arguments.get("days", 30)
    
    # Calculate start time
    now = pd.Timestamp.now(tz='UTC')
    start_ts = int((now - pd.Timedelta(days=days)).timestamp() * 1000)
    
    try:
        exchange = await get_exchange_instance(exchange_id)
        if not exchange.has['fetchOHLCV']:
             return ToolResult(content=[TextContent(text=f"{exchange_id} does not support fetchOHLCV.")])
             
        all_ohlcv = []
        since = start_ts
        
        # Max limit per request usually 1000 for binance
        limit_per_req = 1000
        
        while True:
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, since, limit_per_req)
            if not ohlcv:
                break
            
            all_ohlcv.extend(ohlcv)
            
            # Update since to last timestamp + 1ms
            last_ts = ohlcv[-1][0]
            since = last_ts + 1
            
            # Check if we reached now (allow small buffer)
            if last_ts >= int(now.timestamp() * 1000) - 60000: 
                break
                
            # Rate limit sleep slightly if needed?
            # CCXT usually handles it if enableRateLimit=True
            await asyncio.sleep(exchange.rateLimit / 1000 * 1.1)
            
            # Safety break
            if len(all_ohlcv) > 50000:
                break
                
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        info = f"""### Historical Data Download
**Symbol**: {symbol}
**Exchange**: {exchange_id}
**Timeframe**: {timeframe}
**Total Candles**: {len(df)}
**Range**: {df['datetime'].min()} - {df['datetime'].max()}

Sample (Head/Tail):
{df.head(5).to_markdown()}
...
{df.tail(5).to_markdown()}
"""
        return ToolResult(content=[TextContent(text=info)])
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
