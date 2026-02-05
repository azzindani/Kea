
import ccxt.async_support as ccxt
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
from mcp_servers.ccxt_server.tools.exchange_manager import get_exchange_instance
import pandas as pd
import asyncio

logger = get_logger(__name__)


async def download_history(exchange: str = "binance", symbol: str = "BTC/USDT", timeframe: str = "1h", days: int = 30) -> str:
    """
    Download Historical OHLCV (Pagination).
    Fetches MORE than exchange limit by looping.
    """
    
    # Calculate start time
    now = pd.Timestamp.now(tz='UTC')
    start_ts = int((now - pd.Timedelta(days=days)).timestamp() * 1000)
    
    try:
        ex = await get_exchange_instance(exchange)
        if not ex.has['fetchOHLCV']:
             return f"{exchange} does not support fetchOHLCV."
             
        all_ohlcv = []
        since = start_ts
        
        # Max limit per request usually 1000 for binance
        limit_per_req = 1000
        
        while True:
            ohlcv = await ex.fetch_ohlcv(symbol, timeframe, since, limit_per_req)
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
            await asyncio.sleep(ex.rateLimit / 1000 * 1.1)
            
            # Safety break
            if len(all_ohlcv) > 50000:
                break
                
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        info = f"""### Historical Data Download
**Symbol**: {symbol}
**Exchange**: {exchange}
**Timeframe**: {timeframe}
**Total Candles**: {len(df)}
**Range**: {df['datetime'].min()} - {df['datetime'].max()}

Sample (Head/Tail):
{df.head(5).to_markdown()}
...
{df.tail(5).to_markdown()}
"""
        return info
        
    except Exception as e:
        return f"Error: {str(e)}"

