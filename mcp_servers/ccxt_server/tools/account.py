
import ccxt.async_support as ccxt
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
from mcp_servers.ccxt_server.tools.exchange_manager import get_exchange_instance
import pandas as pd

logger = get_logger(__name__)

async def get_balance(arguments: dict) -> ToolResult:
    """
    Get Account Balance (Requires API Key/Secret via Env or Config).
    Note: Provide keys when initialising exchange or assume user set env vars.
    For this implementation, we assume env vars: 
    CCXT_{EXCHANGE}_API_KEY, CCXT_{EXCHANGE}_SECRET
    """
    exchange_id = arguments.get("exchange")
    
    try:
        # Re-init exchange with keys if needed? 
        # CCXT can read from env if configured, usually manually.
        # But here we use 'get_exchange_instance'.
        # We might need to pass keys in arguments.
        api_key = arguments.get("api_key")
        secret = arguments.get("secret")
        
        exchange = await get_exchange_instance(exchange_id)
        
        if api_key and secret:
            exchange.apiKey = api_key
            exchange.secret = secret
            
        if not exchange.apiKey:
             return ToolResult(isError=True, content=[TextContent(text="API Key/Secret required for get_balance.")])
             
        balance = await exchange.fetch_balance()
        
        # Format 'total' part
        # balance['total'] is dict { 'BTC': 0.1, 'USDT': 100 }
        df = pd.DataFrame(list(balance['total'].items()), columns=['Currency', 'Amount'])
        df = df[df['Amount'] > 0] # Filter zero balances
        
        return ToolResult(content=[TextContent(text=f"### Balance: {exchange_id}\n\n{df.to_markdown()}")])
        
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
