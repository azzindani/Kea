
import ccxt.async_support as ccxt
import ccxt.async_support as ccxt
from shared.logging.main import get_logger
from mcp_servers.ccxt_server.tools.exchange_manager import get_exchange_instance
import pandas as pd

logger = get_logger(__name__)


# --- PRIVATE TOOLS ---

async def get_positions(exchange: str = "binance", api_key: str = None, secret: str = None, symbols: list[str] = None) -> str:
    """
    Get Active Positions (Futures/Perps). Requires API Key.
    """
    try:
        ex = await get_exchange_instance(exchange)
        
        if api_key and secret:
            ex.apiKey = api_key
            ex.secret = secret
            
        if not ex.apiKey:
            return "API Key/Secret required."
            
        if ex.has['fetchPositions']:
            positions = await ex.fetch_positions(symbols)
            if not positions:
                return "No active positions found."
                
            # Flatten
            df = pd.DataFrame(positions)
            # Select key columns
            cols = ['symbol', 'side', 'contracts', 'contractSize', 'unrealizedPnl', 'leverage', 'collateral', 'entryPrice', 'markPrice']
            cols = [c for c in cols if c in df.columns]
            
            return f"### Positions: {exchange}\n\n{df[cols].to_markdown()}"
        else:
             return f"{exchange} does not support fetchPositions."
    except Exception as e:
        return f"Error: {str(e)}"



async def get_open_orders(exchange: str = "binance", symbol: str = None, api_key: str = None, secret: str = None) -> str:
    """
    Get Open Orders. Requires API Key.
    """
    try:
        ex = await get_exchange_instance(exchange)
        if api_key and secret:
            ex.apiKey = api_key
            ex.secret = secret
            
        if not ex.apiKey:
             return "API Key/Secret required."
             
        orders = await ex.fetch_open_orders(symbol)
        if not orders:
            return "No open orders."
            
        df = pd.DataFrame(orders)
        cols = ['id', 'datetime', 'symbol', 'type', 'side', 'price', 'amount', 'filled', 'remaining', 'status']
        cols = [c for c in cols if c in df.columns]
        
        return f"### Open Orders: {exchange} ({symbol or 'All'})\n\n{df[cols].to_markdown()}"
    except Exception as e:
        return f"Error: {str(e)}"



async def get_my_trades(exchange: str = "binance", symbol: str = None, limit: int = 100000, api_key: str = None, secret: str = None) -> str:
    """
    Get My Trades History. Requires API Key.
    """
    try:
        ex = await get_exchange_instance(exchange)
        if api_key and secret:
            ex.apiKey = api_key
            ex.secret = secret
            
        if not ex.apiKey:
             return "API Key/Secret required."
             
        trades = await ex.fetch_my_trades(symbol, limit=limit)
        df = pd.DataFrame(trades)
        cols = ['id', 'datetime', 'symbol', 'side', 'price', 'amount', 'cost', 'fee']
        cols = [c for c in cols if c in df.columns]
        
        return f"### My Trades: {exchange} ({symbol})\n\n{df[cols].to_markdown()}"
    except Exception as e:
        return f"Error: {str(e)}"

