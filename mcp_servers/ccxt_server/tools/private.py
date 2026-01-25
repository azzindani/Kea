
import ccxt.async_support as ccxt
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger
from mcp_servers.ccxt_server.tools.exchange_manager import get_exchange_instance
import pandas as pd

logger = get_logger(__name__)

async def get_positions(arguments: dict) -> ToolResult:
    """
    Get Active Positions (Futures/Perps). Requires API Key.
    """
    exchange_id = arguments.get("exchange", "binance")
    
    try:
        api_key = arguments.get("api_key")
        secret = arguments.get("secret")
        # Optional: symbols filter
        symbols = arguments.get("symbols") # list or None
        
        exchange = await get_exchange_instance(exchange_id)
        
        if api_key and secret:
            exchange.apiKey = api_key
            exchange.secret = secret
            
        if not exchange.apiKey:
            return ToolResult(isError=True, content=[TextContent(text="API Key/Secret required.")])
            
        if exchange.has['fetchPositions']:
            positions = await exchange.fetch_positions(symbols)
            if not positions:
                return ToolResult(content=[TextContent(text="No active positions found.")])
                
            # Flatten
            df = pd.DataFrame(positions)
            # Select key columns
            cols = ['symbol', 'side', 'contracts', 'contractSize', 'unrealizedPnl', 'leverage', 'collateral', 'entryPrice', 'markPrice']
            cols = [c for c in cols if c in df.columns]
            
            return ToolResult(content=[TextContent(text=f"### Positions: {exchange_id}\n\n{df[cols].to_markdown()}")])
        else:
             return ToolResult(content=[TextContent(text=f"{exchange_id} does not support fetchPositions.")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_open_orders(arguments: dict) -> ToolResult:
    """
    Get Open Orders. Requires API Key.
    """
    exchange_id = arguments.get("exchange", "binance")
    symbol = arguments.get("symbol")
    
    try:
        api_key = arguments.get("api_key")
        secret = arguments.get("secret")
        exchange = await get_exchange_instance(exchange_id)
        if api_key and secret:
            exchange.apiKey = api_key
            exchange.secret = secret
            
        if not exchange.apiKey:
             return ToolResult(isError=True, content=[TextContent(text="API Key/Secret required.")])
             
        orders = await exchange.fetch_open_orders(symbol)
        if not orders:
            return ToolResult(content=[TextContent(text="No open orders.")])
            
        df = pd.DataFrame(orders)
        cols = ['id', 'datetime', 'symbol', 'type', 'side', 'price', 'amount', 'filled', 'remaining', 'status']
        cols = [c for c in cols if c in df.columns]
        
        return ToolResult(content=[TextContent(text=f"### Open Orders: {exchange_id} ({symbol or 'All'})\n\n{df[cols].to_markdown()}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])

async def get_my_trades(arguments: dict) -> ToolResult:
    """
    Get My Trades History. Requires API Key.
    """
    exchange_id = arguments.get("exchange", "binance")
    symbol = arguments.get("symbol")
    limit = arguments.get("limit", 20)
    
    try:
        api_key = arguments.get("api_key")
        secret = arguments.get("secret")
        exchange = await get_exchange_instance(exchange_id)
        if api_key and secret:
            exchange.apiKey = api_key
            exchange.secret = secret
            
        if not exchange.apiKey:
             return ToolResult(isError=True, content=[TextContent(text="API Key/Secret required.")])
             
        trades = await exchange.fetch_my_trades(symbol, limit=limit)
        df = pd.DataFrame(trades)
        cols = ['id', 'datetime', 'symbol', 'side', 'price', 'amount', 'cost', 'fee']
        cols = [c for c in cols if c in df.columns]
        
        return ToolResult(content=[TextContent(text=f"### My Trades: {exchange_id} ({symbol})\n\n{df[cols].to_markdown()}")])
    except Exception as e:
        return ToolResult(isError=True, content=[TextContent(text=str(e))])
