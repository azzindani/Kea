from mcp.server.fastmcp import FastMCP
from mcp_servers.ccxt_server.tools import (
    public, metadata, aggregator, derivatives, historical, account, private, trading, exchange_manager
)
import ccxt.async_support as ccxt
import structlog
import asyncio

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("ccxt_server", dependencies=["ccxt", "pandas"])

# --- 1. UNIFIED PUBLIC DATA ---
@mcp.tool()
async def get_ticker(exchange: str, symbol: str) -> str:
    """PUBLIC: Get Ticker (Price, Vol) for any exchange."""
    return await public.get_ticker(exchange, symbol)

@mcp.tool()
async def get_ohlcv(exchange: str, symbol: str, timeframe: str = "1d", limit: int = 100000) -> str:
    """PUBLIC: Get Candles (Open/High/Low/Close)."""
    return await public.get_ohlcv(exchange, symbol, timeframe, limit)

@mcp.tool()
async def get_order_book(exchange: str, symbol: str, limit: int = 100000) -> str:
    """PUBLIC: Get Order Book (Bids/Asks Depth)."""
    return await public.get_order_book(exchange, symbol, limit)

@mcp.tool()
async def get_trades(exchange: str, symbol: str, limit: int = 100000) -> str:
    """PUBLIC: Get Recent Trades."""
    return await public.get_trades(exchange, symbol, limit)

@mcp.tool()
async def get_exchange_status(exchange: str) -> str:
    """PUBLIC: Get Exchange Status."""
    return await public.get_status(exchange)

@mcp.tool()
async def get_exchange_time(exchange: str) -> str:
    """PUBLIC: Get Exchange Time."""
    return await public.get_time(exchange)

# --- 2. AGGREGATOR (MULTITALENT) ---
@mcp.tool()
async def get_global_price(symbol: str = "BTC/USDT", exchanges: list[str] = None) -> str:
    """MACRO: Get Global Price Aggregation (Mean/Spread)."""
    return await aggregator.get_global_price(symbol, exchanges)

@mcp.tool()
async def get_arbitrage_scan(symbol: str = "BTC/USDT", exchanges: list[str] = None) -> str:
    """MACRO: Check Arbitrage (Buy Low/Sell High)."""
    return await aggregator.get_arbitrage_spread(symbol, exchanges)

# --- 3. METADATA ---
@mcp.tool()
async def list_exchange_markets(exchange: str) -> str:
    """META: List all pairs on an exchange."""
    return await metadata.list_exchange_markets(exchange)

@mcp.tool()
async def check_exchange_capabilities(exchange: str) -> str:
    """META: Check what exchange supports (fetchOHLCV, fetchPositions, etc)."""
    return await metadata.get_exchange_capabilities(exchange)

# --- 5. PHASE 2: DERIVATIVES & HISTORY ---
@mcp.tool()
async def get_funding_rate(exchange: str, symbol: str) -> str:
    """DERIVATIVES: Get Funding Rate."""
    return await derivatives.get_funding_rate(exchange, symbol)

@mcp.tool()
async def get_open_interest(exchange: str, symbol: str) -> str:
    """DERIVATIVES: Get Open Interest."""
    return await derivatives.get_open_interest(exchange, symbol)

@mcp.tool()
async def download_market_history(exchange: str, symbol: str, timeframe: str = "1h", days: int = 30) -> str:
    """HISTORY: Download Large History (Pagination)."""
    return await historical.download_history(exchange, symbol, timeframe, days)

@mcp.tool()
async def get_account_balance(exchange: str, api_key: str = None, secret: str = None) -> str:
    """ACCOUNT: Get Balance (API Key Required)."""
    return await account.get_balance(exchange, api_key, secret)

# --- 6. PHASE 3: PRIVATE & ADVANCED ---
@mcp.tool()
async def get_positions(exchange: str, api_key: str, secret: str, symbols: list[str] = None) -> str:
    """PRIVATE: Get Futures Positions."""
    return await private.get_positions(exchange, api_key, secret, symbols)

@mcp.tool()
async def get_open_orders(exchange: str, api_key: str, secret: str, symbol: str = None) -> str:
    """PRIVATE: Get Open Orders."""
    return await private.get_open_orders(exchange, symbol, api_key, secret)

@mcp.tool()
async def get_my_trades_history(exchange: str, api_key: str, secret: str, symbol: str = None, limit: int = 100000) -> str:
    """PRIVATE: Get My Trades."""
    return await private.get_my_trades(exchange, symbol, limit, api_key, secret)

@mcp.tool()
async def get_global_funding_rates(symbol: str = "BTC/USDT", exchanges: list[str] = None) -> str:
    """MACRO: Global Funding Rate Map."""
    return await aggregator.get_global_funding_spread(symbol, exchanges)

# --- 7. PHASE 4: ACTIVE MANAGEMENT ---
@mcp.tool()
async def create_market_order(exchange: str, symbol: str, side: str, amount: float, api_key: str, secret: str) -> str:
    """TRADING: Create MARKET Order (Buy/Sell). CAUTION."""
    return await trading.create_order(exchange, symbol, "market", side, amount, None, api_key, secret)

@mcp.tool()
async def create_limit_order(exchange: str, symbol: str, side: str, amount: float, price: float, api_key: str, secret: str) -> str:
    """TRADING: Create LIMIT Order (Buy/Sell). CAUTION."""
    return await trading.create_order(exchange, symbol, "limit", side, amount, price, api_key, secret)

@mcp.tool()
async def cancel_active_order(exchange: str, id: str, api_key: str, secret: str, symbol: str = None) -> str:
    """TRADING: Cancel Order."""
    return await trading.cancel_order(exchange, id, symbol, api_key, secret)

# --- SHORTCUT TOOLS GENERATOR ---
# We can dynamically register tools for top exchanges to make it easier for the LLM
TOP_EXCHANGES = ['binance', 'kraken', 'coinbase', 'okx', 'bybit', 'kucoin', 'gateio', 'bitstamp']

def register_shortcuts():
    for ex in TOP_EXCHANGES:
        
        # Ticker Shortcut
        async def ticker_handler(symbol: str, _ex=ex) -> str:
            return await public.get_ticker(_ex, symbol)
        
        mcp.add_tool(
            name=f"get_{ex}_ticker",
            description=f"SHORTCUT: Get {ex.title()} Ticker.",
            fn=ticker_handler
        )

        # Order Book Shortcut
        async def book_handler(symbol: str, _ex=ex) -> str:
            return await public.get_order_book(_ex, symbol)
        
        mcp.add_tool(
            name=f"get_{ex}_book",
            description=f"SHORTCUT: Get {ex.title()} Order Book.",
            fn=book_handler
        )
        
        # OHLCV Shortcut
        async def ohlcv_handler(symbol: str, _ex=ex) -> str:
            return await public.get_ohlcv(_ex, symbol)
            
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

if __name__ == "__main__":
    mcp.run()
