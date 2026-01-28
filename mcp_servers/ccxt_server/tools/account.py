
import ccxt.async_support as ccxt
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
from mcp_servers.ccxt_server.tools.exchange_manager import get_exchange_instance
import pandas as pd

logger = get_logger(__name__)


async def get_balance(exchange: str, api_key: str = None, secret: str = None) -> str:
    """
    Get Account Balance (Requires API Key/Secret via Env or Config).
    Note: Provide keys when initialising exchange or assume user set env vars.
    For this implementation, we assume env vars: 
    CCXT_{EXCHANGE}_API_KEY, CCXT_{EXCHANGE}_SECRET
    """
    
    try:
        # Re-init exchange with keys if needed? 
        # CCXT can read from env if configured, usually manually.
        # But here we use 'get_exchange_instance'.
        # We might need to pass keys in arguments.
        
        ex = await get_exchange_instance(exchange)
        
        if api_key and secret:
            ex.apiKey = api_key
            ex.secret = secret
            
        if not ex.apiKey:
             return "API Key/Secret required for get_balance."
             
        balance = await ex.fetch_balance()
        
        # Format 'total' part
        # balance['total'] is dict { 'BTC': 0.1, 'USDT': 100 }
        df = pd.DataFrame(list(balance['total'].items()), columns=['Currency', 'Amount'])
        df = df[df['Amount'] > 0] # Filter zero balances
        
        return f"### Balance: {exchange}\n\n{df.to_markdown()}"
        
    except Exception as e:
        return f"Error: {str(e)}"

