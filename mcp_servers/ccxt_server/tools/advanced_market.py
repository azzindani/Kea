
import ccxt.async_support as ccxt
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging.main import get_logger
from mcp_servers.ccxt_server.tools.exchange_manager import get_exchange_instance
import pandas as pd

logger = get_logger(__name__)

async def get_liquidations(arguments: dict) -> ToolResult:
    """
    Get Recent Liquidations (Unified or Public).
    """
    exchange_id = arguments.get("exchange", "binance")
    symbol = arguments.get("symbol")
    limit = arguments.get("limit", 20)
    
    try:
        exchange = await get_exchange_instance(exchange_id)
        if hasattr(exchange, 'fetchLiquidations'):
            liqs = await exchange.fetch_liquidations(symbol, limit=limit)
            df = pd.DataFrame(liqs)
            # keys usually: symbol, price, quantity, timestamp, side (who got rekt)
            return ToolResult(content=[TextContent(text=f"### Liquidations: {symbol} on {exchange_id}\n\n{df.tail(limit).to_markdown()}")])
        else:
             return ToolResult(content=[TextContent(text=f"{exchange_id} does not support fetchLiquidations.")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_long_short_ratio(arguments: dict) -> ToolResult:
    """
    Get Long/Short Ratio (Sentiment).
    """
    exchange_id = arguments.get("exchange", "binance")
    symbol = arguments.get("symbol")
    timeframe = arguments.get("timeframe", "1h") # Some exchanges require timeframe
    
    try:
        exchange = await get_exchange_instance(exchange_id)
        if hasattr(exchange, 'fetchLongShortRatio'):
            ls = await exchange.fetch_long_short_ratio(symbol, timeframe)
            # ls: longAccount, shortAccount, longShortRatio, timestamp
            df = pd.DataFrame([ls])
            return ToolResult(content=[TextContent(text=f"### Long/Short Ratio: {symbol} ({timeframe})\n\n{df.to_markdown()}")])
        else:
             return ToolResult(content=[TextContent(text=f"{exchange_id} does not support fetchLongShortRatio.")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
