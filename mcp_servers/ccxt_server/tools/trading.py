
import ccxt.async_support as ccxt
import ccxt.async_support as ccxt
from shared.logging.main import get_logger
from mcp_servers.ccxt_server.tools.exchange_manager import get_exchange_instance
import json

logger = get_logger(__name__)


# --- TRADING TOOLS ---

async def create_order(
    exchange: str,
    symbol: str, 
    type: str, 
    side: str, 
    amount: float, 
    price: float = None, 
    api_key: str = None, 
    secret: str = None
) -> str:
    """
    Create Order (Buy/Sell). CAUTION: Executes real trade.
    Requires: api_key, secret, symbol, type (market/limit), side (buy/sell), amount, price (if limit).
    """
    try:
        ex = await get_exchange_instance(exchange)
        if api_key and secret:
            ex.apiKey = api_key
            ex.secret = secret
            
        if not ex.apiKey:
             return "API Key/Secret required."
             
        order = await ex.create_order(symbol, type, side, float(amount), float(price) if price else None)
        
        # Order result structure
        return f"### Order Created: {exchange}\n```json\n{json.dumps(order, indent=2, default=str)}\n```"
        
    except Exception as e:
        return f"Error: {str(e)}"



async def cancel_order(exchange: str, id: str, symbol: str = None, api_key: str = None, secret: str = None) -> str:
    """
    Cancel Order.
    Requires: id (order id), symbol (often required).
    """
    try:
        ex = await get_exchange_instance(exchange)
        if api_key and secret:
            ex.apiKey = api_key
            ex.secret = secret
            
        if not ex.apiKey:
             return "API Key/Secret required."
             
        res = await ex.cancel_order(id, symbol)
        return f"### Order Cancelled: {id}\n```json\n{json.dumps(res, indent=2, default=str)}\n```"
        
    except Exception as e:
        return f"Error: {str(e)}"

