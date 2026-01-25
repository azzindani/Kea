
import ccxt.async_support as ccxt
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
from mcp_servers.ccxt_server.tools.exchange_manager import get_exchange_instance
import json

logger = get_logger(__name__)

async def create_order(arguments: dict) -> ToolResult:
    """
    Create Order (Buy/Sell). CAUTION: Executes real trade.
    Requires: api_key, secret, symbol, type (market/limit), side (buy/sell), amount, price (if limit).
    """
    exchange_id = arguments.get("exchange", "binance")
    symbol = arguments.get("symbol")
    type_ = arguments.get("type") # market, limit
    side = arguments.get("side") # buy, sell
    amount = float(arguments.get("amount"))
    price = arguments.get("price") # float or None
    if price: price = float(price)
    
    api_key = arguments.get("api_key")
    secret = arguments.get("secret")
    
    try:
        exchange = await get_exchange_instance(exchange_id)
        if api_key and secret:
            exchange.apiKey = api_key
            exchange.secret = secret
            
        if not exchange.apiKey:
             return ToolResult(isError=True, content=[TextContent(text="API Key/Secret required.")])
             
        order = await exchange.create_order(symbol, type_, side, amount, price)
        
        # Order result structure
        # id, clientOrderId, timestamp, status, symbol, type, side, price, amount...
        return ToolResult(content=[TextContent(text=f"### Order Created: {exchange_id}\n```json\n{json.dumps(order, indent=2, default=str)}\n```")])
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def cancel_order(arguments: dict) -> ToolResult:
    """
    Cancel Order.
    Requires: id (order id), symbol (often required).
    """
    exchange_id = arguments.get("exchange", "binance")
    id_ = arguments.get("id")
    symbol = arguments.get("symbol")
    
    api_key = arguments.get("api_key")
    secret = arguments.get("secret")
    
    try:
        exchange = await get_exchange_instance(exchange_id)
        if api_key and secret:
            exchange.apiKey = api_key
            exchange.secret = secret
            
        if not exchange.apiKey:
             return ToolResult(isError=True, content=[TextContent(text="API Key/Secret required.")])
             
        res = await exchange.cancel_order(id_, symbol)
        return ToolResult(content=[TextContent(text=f"### Order Cancelled: {id_}\n```json\n{json.dumps(res, indent=2, default=str)}\n```")])
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
