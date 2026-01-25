
import ccxt.async_support as ccxt
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
from mcp_servers.ccxt_server.tools.exchange_manager import get_exchange_instance
import pandas as pd

logger = get_logger(__name__)

async def get_funding_rate(arguments: dict) -> ToolResult:
    """
    Get Funding Rate (Futures/Perps).
    """
    exchange_id = arguments.get("exchange", "binance")
    symbol = arguments.get("symbol") # e.g. BTC/USDT:USDT
    
    try:
        exchange = await get_exchange_instance(exchange_id)
        if hasattr(exchange, 'fetchFundingRate'):
            rate = await exchange.fetch_funding_rate(symbol)
            # Flatten
            # usually has: fundingRate, timestamp, nextFundingTime
            df = pd.DataFrame([rate])
            cols = ['symbol', 'fundingRate', 'timestamp', 'datetime', 'nextFundingTime', 'nextFundingRate']
            cols = [c for c in cols if c in df.columns]
            return ToolResult(content=[TextContent(text=f"### Funding Rate: {symbol} on {exchange_id}\n\n{df[cols].to_markdown()}")])
        else:
            return ToolResult(content=[TextContent(text=f"{exchange_id} does not support fetchFundingRate.")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_open_interest(arguments: dict) -> ToolResult:
    """
    Get Open Interest (Futures/Perps).
    """
    exchange_id = arguments.get("exchange", "binance")
    symbol = arguments.get("symbol")
    
    try:
        exchange = await get_exchange_instance(exchange_id)
        if hasattr(exchange, 'fetchOpenInterest'):
            oi = await exchange.fetch_open_interest(symbol)
            # oi keys: symbol, openInterestAmount, openInterestValue, timestamp
            df = pd.DataFrame([oi])
            return ToolResult(content=[TextContent(text=f"### Open Interest: {symbol}\n\n{df.to_markdown()}")])
        else:
             return ToolResult(content=[TextContent(text=f"{exchange_id} does not support fetchOpenInterest.")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
