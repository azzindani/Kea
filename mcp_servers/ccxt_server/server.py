
from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parents[2]))
from mcp_servers.ccxt_server.tools import (
    public, metadata, aggregator, derivatives, historical, account, private, trading, exchange_manager
)
import ccxt.async_support as ccxt
import structlog
import asyncio

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging.structured import setup_logging
setup_logging()

mcp = FastMCP("ccxt_server", dependencies=["ccxt", "pandas"])

# --- 1. UNIFIED PUBLIC DATA ---
@mcp.tool()
async def get_ticker(exchange: str, symbol: str) -> str:
    """FETCHES ticker data. [ACTION]
    
    [RAG Context]
    Gets current price, volume, and 24h stats for any exchange.
    Returns ticker object.
    """
    return await public.get_ticker(exchange, symbol)

@mcp.tool()
async def get_ohlcv(exchange: str, symbol: str, timeframe: str = "1d", limit: int = 100000) -> str:
    """FETCHES OHLCV candles. [ACTION]
    
    [RAG Context]
    Gets historical candlestick data (Open, High, Low, Close, Volume).
    Returns list of candles.
    """
    return await public.get_ohlcv(exchange, symbol, timeframe, limit)

@mcp.tool()
async def get_order_book(exchange: str, symbol: str, limit: int = 100000) -> str:
    """FETCHES order book. [ACTION]
    
    [RAG Context]
    Gets current bids and asks depth.
    Returns order book object.
    """
    return await public.get_order_book(exchange, symbol, limit)

@mcp.tool()
async def get_trades(exchange: str, symbol: str, limit: int = 100000) -> str:
    """FETCHES recent trades. [ACTION]
    
    [RAG Context]
    Gets list of most recent public trades.
    Returns list of trades.
    """
    return await public.get_trades(exchange, symbol, limit)

@mcp.tool()
async def get_exchange_status(exchange: str) -> str:
    """CHECKS exchange status. [ACTION]
    
    [RAG Context]
    Checks if exchange is online/maintenance.
    Returns status object.
    """
    return await public.get_status(exchange)

@mcp.tool()
async def get_exchange_time(exchange: str) -> str:
    """FETCHES exchange time. [ACTION]
    
    [RAG Context]
    Gets server time from exchange.
    Returns time object.
    """
    return await public.get_time(exchange)

# --- 2. AGGREGATOR (MULTITALENT) ---
@mcp.tool()
async def get_global_price(symbol: str = "BTC/USDT", exchanges: list[str] = None) -> str:
    """AGGREGATES global price. [ACTION]
    
    [RAG Context]
    Calculates mean price and spread across multiple exchanges.
    Returns aggregated stats.
    """
    return await aggregator.get_global_price(symbol, exchanges)

@mcp.tool()
async def get_arbitrage_scan(symbol: str = "BTC/USDT", exchanges: list[str] = None) -> str:
    """SCANS for arbitrage. [ACTION]
    
    [RAG Context]
    Checks for price differences (Buy Low/Sell High) across exchanges.
    Returns arbitrage opportunities.
    """
    return await aggregator.get_arbitrage_spread(symbol, exchanges)

# --- 3. METADATA ---
@mcp.tool()
async def list_exchange_markets(exchange: str) -> str:
    """LISTS exchange markets. [ACTION]
    
    [RAG Context]
    Lists all trading pairs available on an exchange.
    Returns list of symbols.
    """
    return await metadata.list_exchange_markets(exchange)

@mcp.tool()
async def check_exchange_capabilities(exchange: str) -> str:
    """CHECKS exchange capabilities. [ACTION]
    
    [RAG Context]
    Checks what features exchange supports (fetchOHLCV, fetchPositions, etc).
    Returns capabilities object.
    """
    return await metadata.get_exchange_capabilities(exchange)

# --- 5. PHASE 2: DERIVATIVES & HISTORY ---
@mcp.tool()
async def get_funding_rate(exchange: str, symbol: str) -> str:
    """FETCHES funding rate. [ACTION]
    
    [RAG Context]
    Gets current funding rate for perpetual futures.
    Returns funding rate object.
    """
    return await derivatives.get_funding_rate(exchange, symbol)

@mcp.tool()
async def get_open_interest(exchange: str, symbol: str) -> str:
    """FETCHES open interest. [ACTION]
    
    [RAG Context]
    Gets total open interest for a contract.
    Returns open interest object.
    """
    return await derivatives.get_open_interest(exchange, symbol)

@mcp.tool()
async def download_market_history(exchange: str, symbol: str, timeframe: str = "1h", days: int = 30) -> str:
    """DOWNLOADS deep history. [ACTION]
    
    [RAG Context]
    Downloads large historical datasets via pagination.
    Returns path to saved file or summary.
    """
    return await historical.download_history(exchange, symbol, timeframe, days)

@mcp.tool()
async def get_account_balance(exchange: str, api_key: str = None, secret: str = None) -> str:
    """FETCHES account balance. [ACTION]
    
    [RAG Context]
    Gets user account balance (requires API key).
    Returns balance object.
    """
    return await account.get_balance(exchange, api_key, secret)

# --- 6. PHASE 3: PRIVATE & ADVANCED ---
@mcp.tool()
async def get_positions(exchange: str, api_key: str, secret: str, symbols: list[str] = None) -> str:
    """FETCHES positions. [ACTION]
    
    [RAG Context]
    Gets current open positions (futures/margin).
    Returns list of positions.
    """
    return await private.get_positions(exchange, api_key, secret, symbols)

@mcp.tool()
async def get_open_orders(exchange: str, api_key: str, secret: str, symbol: str = None) -> str:
    """FETCHES open orders. [ACTION]
    
    [RAG Context]
    Gets currently active open orders.
    Returns list of orders.
    """
    return await private.get_open_orders(exchange, symbol, api_key, secret)

@mcp.tool()
async def get_my_trades_history(exchange: str, api_key: str, secret: str, symbol: str = None, limit: int = 100000) -> str:
    """FETCHES trade history. [ACTION]
    
    [RAG Context]
    Gets user's past trade history.
    Returns list of trades.
    """
    return await private.get_my_trades(exchange, symbol, limit, api_key, secret)

@mcp.tool()
async def get_global_funding_rates(symbol: str = "BTC/USDT", exchanges: list[str] = None) -> str:
    """AGGREGATES funding rates. [ACTION]
    
    [RAG Context]
    Compare funding rates across multiple exchanges.
    Returns funding rate map.
    """
    return await aggregator.get_global_funding_spread(symbol, exchanges)

# --- 7. PHASE 4: ACTIVE MANAGEMENT ---
@mcp.tool()
async def create_market_order(exchange: str, symbol: str, side: str, amount: float, api_key: str, secret: str) -> str:
    """EXECUTES market order. [ACTION]
    
    [RAG Context]
    Places a market buy/sell order. CAUTION: Executes immediately at current price.
    Returns order result.
    """
    return await trading.create_order(exchange, symbol, "market", side, amount, None, api_key, secret)

@mcp.tool()
async def create_limit_order(exchange: str, symbol: str, side: str, amount: float, price: float, api_key: str, secret: str) -> str:
    """EXECUTES limit order. [ACTION]
    
    [RAG Context]
    Places a limit buy/sell order at specific price.
    Returns order result.
    """
    return await trading.create_order(exchange, symbol, "limit", side, amount, price, api_key, secret)

@mcp.tool()
async def cancel_active_order(exchange: str, id: str, api_key: str, secret: str, symbol: str = None) -> str:
    """CANCELS order. [ACTION]
    
    [RAG Context]
    Cancels an active order by ID.
    Returns cancellation result.
    """
    return await trading.cancel_order(exchange, id, symbol, api_key, secret)

# --- SHORTCUT TOOLS GENERATOR ---
# We can dynamically register tools for top exchanges to make it easier for the LLM
TOP_EXCHANGES = ['binance', 'kraken', 'coinbase', 'okx', 'bybit', 'kucoin', 'gateio', 'bitstamp']

def register_shortcuts():
    for ex in TOP_EXCHANGES:
        
        # Ticker Shortcut
        async def ticker_handler(symbol: str, exchange_name=ex) -> str:
            return await public.get_ticker(exchange_name, symbol)
        
        mcp.add_tool(
            name=f"get_{ex}_ticker",
            description=f"SHORTCUT: Get {ex.title()} Ticker.",
            fn=ticker_handler
        )

        # Order Book Shortcut
        async def book_handler(symbol: str, exchange_name=ex) -> str:
            return await public.get_order_book(exchange_name, symbol)
        
        mcp.add_tool(
            name=f"get_{ex}_book",
            description=f"SHORTCUT: Get {ex.title()} Order Book.",
            fn=book_handler
        )
        
        # OHLCV Shortcut
        async def ohlcv_handler(symbol: str, exchange_name=ex) -> str:
            return await public.get_ohlcv(exchange_name, symbol)
            
        mcp.add_tool(
            name=f"get_{ex}_ohlcv",
            description=f"SHORTCUT: Get {ex.title()} Candles.",
            fn=ohlcv_handler
        )

register_shortcuts()  

@mcp.tool()
async def list_all_supported_exchanges() -> str:
    """META: List all supported CCXT exchanges (~100+)."""
    return str(ccxt.exchanges)

@mcp.tool()
async def cleanup_resources() -> str:
    """CLEANS UP resources. [ACTION]
    
    [RAG Context]
    Closes all active exchange connections.
    """
    await exchange_manager.ExchangeManager.close_all()
    return "Resources cleaned up."

if __name__ == "__main__":
    mcp.run()

# ==========================================
# Compatibility Layer for Tests
# ==========================================
class CcxtServer:
    def __init__(self):
        # Wrap the FastMCP instance
        self.mcp = mcp

    def get_tools(self):
        # Access internal tool manager to get list of tool objects
        # We need to return objects that have a .name attribute
        if hasattr(self.mcp, '_tool_manager') and hasattr(self.mcp._tool_manager, '_tools'):
            return list(self.mcp._tool_manager._tools.values())
        return []
