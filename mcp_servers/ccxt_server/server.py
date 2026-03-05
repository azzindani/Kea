
from shared.mcp.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parents[2]))
from mcp_servers.ccxt_server.tools import (
    public, metadata, aggregator, derivatives, historical, account, private, trading, exchange_manager
)
from typing import List, Dict, Any, Optional
from shared.logging.main import setup_logging, get_logger
import ccxt.async_support as ccxt
import asyncio

setup_logging(force_stderr=True)
logger = get_logger(__name__)

# Create the FastMCP server

mcp = FastMCP("ccxt_server", dependencies=["ccxt", "pandas"])

# --- 1. UNIFIED PUBLIC DATA ---
@mcp.tool()
async def get_ticker(exchange: str, symbol: str) -> str:
    """FETCHES ticker data. [ACTION]
    
    [RAG Context]
    Retrieves the most recent price snapshot for a specific cryptocurrency trading pair from a unified exchange interface. CCXT supports over 100 exchanges (Binance, Kraken, Bybit, etc.).
    
    How to Use:
    - Pass the exchange name (lowercase) and the trading pair (e.g., 'binance', 'BTC/USDT').
    - Returns Last Price, Bid, Ask, 24h High, 24h Low, and 24h Volume.
    - Essential for real-time crypto price tracking and spread analysis.
    
    Arguments:
    - exchange (str): lowercase exchange ID (e.g., 'binance', 'kraken', 'okx').
    - symbol (str): The common pair format: 'BASE/QUOTE' (e.g., 'ETH/BTC', 'SOL/USDT').
    
    Keywords: crypto price, bitcoin quote, ethereum value, exchange ticker, real-time crypto.
    """
    return await public.get_ticker(exchange, symbol)

@mcp.tool()
async def get_ohlcv(exchange: str, symbol: str, timeframe: str = "1d", limit: int = 100000) -> str:
    """FETCHES OHLCV candles. [ACTION]
    
    [RAG Context]
    Retrieves historical candlestick data for technical analysis. This is the cornerstone for building charts or running automated trading strategies.
    
    How to Use:
    - Specify the 'timeframe' (e.g., '1m', '5m', '15m', '1h', '4h', '1d', '1w', '1M').
    - 'limit' controls how many previous candles to fetch.
    - Format: [[timestamp, open, high, low, close, volume], ...]
    
    Arguments:
    - exchange (str): The exchange ID.
    - symbol (str): The trading pair.
    - timeframe (str): Frequency of candles.
    - limit (int): Number of items to retrieve.
    
    Keywords: crypto candles, price history, technical analysis, historical crypto data, charting data.
    """
    return await public.get_ohlcv(exchange, symbol, timeframe, limit)

@mcp.tool()
async def get_order_book(exchange: str, symbol: str, limit: int = 100000) -> str:
    """FETCHES order book. [ACTION]
    
    [RAG Context]
    Returns the current Bids (buy orders) and Asks (sell orders) depth for a market. Essential for measuring liquidity and slippage before large trades.
    
    How to Use:
    - Lists the top N levels of the book.
    - Compare high-side asks and low-side bids to calculate the "Bid-Ask Spread".
    
    Arguments:
    - exchange (str): The exchange ID.
    - symbol (str): The pair.
    - limit (int): Number of depth levels.
    
    Keywords: l2 depth, liquidity, bid ask spread, market depth, order book.
    """
    return await public.get_order_book(exchange, symbol, limit)

@mcp.tool()
async def get_trades(exchange: str, symbol: str, limit: int = 100000) -> str:
    """FETCHES recent trades. [ACTION]
    
    [RAG Context]
    Retrieves the most recent executions in the public market.
    
    How to Use:
    - Use this to track selling/buying pressure in real-time.
    - Returns a list of trade objects with timestamp, side (buy/sell), price, and amount.
    
    Arguments:
    - exchange (str): The exchange ID.
    - symbol (str): The trading pair.
    
    Keywords: trade history, market tape, recent executions, crypto volume tracking.
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
    A "Super Tool" that calculates the average price of an asset across multiple exchanges. This is critical for discovering the true "Fair Market Value" of a cryptocurrency and identifying price imbalances.
    
    How to Use:
    - Pass the symbol (e.g., 'BTC/USDT').
    - Optionally specify a list of exchanges: ['binance', 'kraken', 'okx'].
    - Useful for avoiding exchange-specific price anomalies.
    
    Arguments:
    - symbol: Pair to check.
    - exchanges: List of exchange IDs.
    
    Keywords: weighted average price, global crypto rate, mean price across exchanges.
    """
    return await aggregator.get_global_price(symbol, exchanges)

@mcp.tool()
async def get_arbitrage_scan(symbol: str = "BTC/USDT", exchanges: list[str] = None) -> str:
    """SCANS for arbitrage. [ACTION]
    
    [RAG Context]
    High-value tool for traders that identifies "Price Spreads" between different exchanges. It looks for the Lowest Ask (cheapest to buy) and the Highest Bid (most expensive to sell) in the market.
    
    How to Use:
    - Use this to find profit opportunities ("Buy Low on Exchange A, Sell High on Exchange B").
    - Result includes the % spread. Note: Does not include withdrawal fees.
    
    Arguments:
    - symbol: The target pair.
    
    Keywords: arbitrage, price spread, cross-exchange, profit opportunity, risk-free trade.
    """
    return await aggregator.get_arbitrage_spread(symbol, exchanges)

# --- 3. METADATA ---
@mcp.tool()
async def list_exchange_markets(exchange: str) -> str:
    """LISTS exchange markets. [ACTION]
    
    [RAG Context]
    Exploratory tool to discover all trading symbols available on a specific exchange. 
    
    How to Use:
    - Call this if you're unsure if an exchange supports a specific altcoin (e.g., 'SOL/USDC').
    - Use as a prerequisite for other data-fetching tools to avoid 'SymbolNotFound' errors.
    
    Arguments:
    - exchange: Lowercase exchange ID.
    
    Keywords: discover markets, available pairs, tradeable symbols, exchange listing.
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
    Retrieves the total number of outstanding derivative contracts (futures or options) that have not been settled. 
    
    How to Use:
    - High open interest indicates high market participation and trend strength.
    - Decreasing open interest may signal a trend reversal.
    - Essential for sentiment analysis in crypto futures markets.
    
    Keywords: futures demand, market participation, contract volume, open interest.
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
    Retrieves the current asset balances for a private exchange account. requires valid API credentials (API Key and Secret).
    
    How to Use:
    - Returns a breakdown of 'Free' (available), 'Used' (locked in orders), and 'Total' funds for all currencies.
    - Crucial for risk management and verifying if enough funds exist for a trade.
    
    Keywords: wallet balance, account funds, asset breakdown, private balance.
    """
    return await account.get_balance(exchange, api_key, secret)

# --- 6. PHASE 3: PRIVATE & ADVANCED ---
@mcp.tool()
async def get_positions(exchange: str, api_key: str, secret: str, symbols: list[str] = None) -> str:
    """FETCHES positions. [ACTION]
    
    [RAG Context]
    Retrieves active futures or margin positions for the user's account. Requires API credentials with 'trade' permissions.
    
    How to Use:
    - Provides Entry Price, Size, Leverage, Liquidation Price, and Unrealized PnL (Profit/Loss).
    - Use this to monitor active risk and decide on closing or trimming positions.
    
    Keywords: active trades, margin positions, futures pnl, liquidation risk.
    """
    return await private.get_positions(exchange, api_key, secret, symbols)

@mcp.tool()
async def get_open_orders(exchange: str, api_key: str, secret: str, symbol: str = None) -> str:
    """FETCHES open orders. [ACTION]
    
    [RAG Context]
    Retrieves the list of active buy/sell orders that are currently waiting in the exchange's order book and have not yet been filled.
    
    How to Use:
    - Crucial for monitoring active exposure and deciding if existing limit orders need to be cancelled or modified.
    - Requires 'fetchOpenOrders' permission on the API key.
    
    Keywords: pending orders, limit orders, active trade desk, cancel management.
    """
    return await private.get_open_orders(exchange, symbol, api_key, secret)

@mcp.tool()
async def get_my_trades_history(exchange: str, api_key: str, secret: str, symbol: str = None, limit: int = 100000) -> str:
    """FETCHES trade history. [ACTION]
    
    [RAG Context]
    Retrieves the private execution history for the current user's account. This is distinct from public trades as it only shows the user's specific fills.
    
    How to Use:
    - Use this to audits past performance, calculate taxes, or verify trade reconciliation.
    - 'symbol' can be used to filter for a specific pair.
    
    Keywords: execution logs, fill history, my trades, portfolio auditing.
    """
    return await private.get_my_trades(exchange, symbol, limit, api_key, secret)

@mcp.tool()
async def get_global_funding_rates(symbol: str = "BTC/USDT", exchanges: list[str] = None) -> str:
    """AGGREGATES funding rates. [ACTION]
    
    [RAG Context]
    A "Super Tool" that compares perpetual futures funding rates across multiple top-tier exchanges simultaneously (Binance, Bybit, OKX, Kraken).
    
    How to Use:
    - Essential for 'Funding Arbitrage' strategies. Seek markets with the highest positive/negative rates for profitable positioning.
    - Provides a global heat-map of market sentiment (Positive = Longs pay Shorts, Negative = Shorts pay Longs).
    
    Keywords: funding arbitrage, sentiment heatmap, cross-exchange, futures rates.
    """
    return await aggregator.get_global_funding_spread(symbol, exchanges)

# --- 7. PHASE 4: ACTIVE MANAGEMENT ---
@mcp.tool()
async def create_market_order(exchange: str, symbol: str, side: str, amount: float, api_key: str, secret: str) -> str:
    """EXECUTES market order. [ACTION]
    
    [RAG Context]
    Instructs the exchange to immediately Buy or Sell a specific amount of an asset at the best available current market price. 
    
    CAUTION: 
    - Market orders are filled instantly but may suffer from 'Slippage' (average price worse than current mid-market) especially in low-liquidity markets.
    - Never use market orders for extremely large positions relative to the order book depth.
    
    Keywords: buy now, sell now, instant execution, market filler.
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
    Attempts to cancel an active, unfilled, or partially filled limit order on the exchange.
    
    How to Use:
    - Requires the 'id' of the order (provided when creating the order).
    - If the order is already fully filled, this will return an error or a 'canceled_already' status.
    
    Keywords: stop order, abort trade, kill order, order removal.
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
    """META: List all supported CCXT exchanges (~100+). [DATA]
    
    [RAG Context]
    Returns a full list of exchange IDs that CCXT currently supports. This is the global library manifest. 
    
    Keywords: exchange list, supported platforms, ccxt manifest.
    """
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

