
from __future__ import annotations
import asyncio
from shared.mcp.server_base import MCPServer
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

# Tools
from mcp_servers.ccxt_server.tools.public import get_ticker, get_ohlcv, get_order_book
from mcp_servers.ccxt_server.tools.metadata import list_exchange_markets, get_exchange_capabilities
from mcp_servers.ccxt_server.tools.aggregator import get_global_price, get_arbitrage_spread
from mcp_servers.ccxt_server.tools.exchange_manager import ExchangeManager
import ccxt

logger = get_logger(__name__)

class CcxtServer(MCPServer):
    """
    CCXT (Crypto) MCP Server.
    Unified Access to 100+ Cryptocurrency Exchanges.
    """
    
    def __init__(self) -> None:
        super().__init__(name="ccxt_server", version="1.0.0")
        self._register_tools()
        
    def _register_tools(self) -> None:
        
        # --- 1. UNIFIED PUBLIC DATA ---
        self.register_tool(
            name="get_ticker", description="PUBLIC: Get Ticker (Price, Vol) for any exchange.",
            handler=get_ticker, parameters={"exchange": {"type": "string"}, "symbol": {"type": "string"}}
        )
        self.register_tool(
            name="get_ohlcv", description="PUBLIC: Get Candles (Open/High/Low/Close).",
            handler=get_ohlcv, parameters={"exchange": {"type": "string"}, "symbol": {"type": "string"}, "timeframe": {"type": "string"}, "limit": {"type": "integer"}}
        )
        self.register_tool(
            name="get_order_book", description="PUBLIC: Get Order Book (Bids/Asks Depth).",
            handler=get_order_book, parameters={"exchange": {"type": "string"}, "symbol": {"type": "string"}, "limit": {"type": "integer"}}
        )
        # New Tools
        from mcp_servers.ccxt_server.tools.public import get_trades, get_status, get_time
        self.register_tool(
            name="get_trades", description="PUBLIC: Get Recent Trades.",
            handler=get_trades, parameters={"exchange": {"type": "string"}, "symbol": {"type": "string"}, "limit": {"type": "integer"}}
        )
        self.register_tool(
            name="get_status", description="PUBLIC: Get Exchange Status.",
            handler=get_status, parameters={"exchange": {"type": "string"}}
        )
        self.register_tool(
            name="get_time", description="PUBLIC: Get Exchange Time.",
            handler=get_time, parameters={"exchange": {"type": "string"}}
        )
        
        # --- 2. AGGREGATOR (MULTITALENT) ---
        self.register_tool(
            name="get_global_price", description="MACRO: Get Global Price Aggregation (Mean/Spread).",
            handler=get_global_price, parameters={"symbol": {"type": "string"}, "exchanges": {"type": "array"}}
        )
        self.register_tool(
            name="get_arbitrage_spread", description="MACRO: Check Arbitrage (Buy Low/Sell High).",
            handler=get_arbitrage_spread, parameters={"symbol": {"type": "string"}}
        )
        
        # --- 3. METADATA ---
        self.register_tool(
            name="list_exchange_markets", description="META: List all pairs on an exchange.",
            handler=list_exchange_markets, parameters={"exchange": {"type": "string"}}
        )
        self.register_tool(
            name="get_exchange_capabilities", description="META: Check what exchange supports (fetchOHLCV?).",
            handler=get_exchange_capabilities, parameters={"exchange": {"type": "string"}}
        )
        
        # --- 5. PHASE 2: DERIVATIVES & HISTORY ---
        from mcp_servers.ccxt_server.tools.derivatives import get_funding_rate, get_open_interest
        from mcp_servers.ccxt_server.tools.historical import download_history
        from mcp_servers.ccxt_server.tools.account import get_balance
        
        self.register_tool(
            name="get_funding_rate", description="DERIVATIVES: Get Funding Rate.",
            handler=get_funding_rate, parameters={"exchange": {"type": "string"}, "symbol": {"type": "string"}}
        )
        self.register_tool(
            name="get_open_interest", description="DERIVATIVES: Get Open Interest.",
            handler=get_open_interest, parameters={"exchange": {"type": "string"}, "symbol": {"type": "string"}}
        )
        self.register_tool(
            name="download_history", description="HISTORY: Download 10k+ Candles (Pagination).",
            handler=download_history, parameters={"exchange": {"type": "string"}, "symbol": {"type": "string"}, "timeframe": {"type": "string"}, "days": {"type": "integer"}}
        )
        self.register_tool(
            name="get_balance", description="ACCOUNT: Get Balance (API Key Required).",
            handler=get_balance, parameters={"exchange": {"type": "string"}, "api_key": {"type": "string"}, "secret": {"type": "string"}}
        )

        # --- 6. PHASE 3: PRIVATE & ADVANCED ---
        from mcp_servers.ccxt_server.tools.private import get_positions, get_open_orders, get_my_trades
        from mcp_servers.ccxt_server.tools.advanced_market import get_liquidations, get_long_short_ratio
        from mcp_servers.ccxt_server.tools.aggregator import get_global_funding_spread
        
        self.register_tool(name="get_positions", description="PRIVATE: Get Futures Positions.", handler=get_positions, parameters={"exchange": {"type": "string"}, "api_key": {"type": "string"}, "secret": {"type": "string"}})
        self.register_tool(name="get_open_orders", description="PRIVATE: Get Open Orders.", handler=get_open_orders, parameters={"exchange": {"type": "string"}, "symbol": {"type": "string"}, "api_key": {"type": "string"}, "secret": {"type": "string"}})
        self.register_tool(name="get_my_trades", description="PRIVATE: Get My Trades.", handler=get_my_trades, parameters={"exchange": {"type": "string"}, "symbol": {"type": "string"}, "api_key": {"type": "string"}, "secret": {"type": "string"}})
        
        self.register_tool(name="get_liquidations", description="MARKET: Get Recent Liquidations.", handler=get_liquidations, parameters={"exchange": {"type": "string"}, "symbol": {"type": "string"}})
        self.register_tool(name="get_long_short_ratio", description="MARKET: Get Long/Short Ratio.", handler=get_long_short_ratio, parameters={"exchange": {"type": "string"}, "symbol": {"type": "string"}, "timeframe": {"type": "string"}})
        self.register_tool(name="get_global_funding_spread", description="MACRO: Global Funding Rate Map.", handler=get_global_funding_spread, parameters={"symbol": {"type": "string"}})

        # --- 7. PHASE 4: ACTIVE MANAGEMENT ---
        from mcp_servers.ccxt_server.tools.ledger import get_transaction_history, get_deposit_address
        from mcp_servers.ccxt_server.tools.margin import get_borrow_rates, get_leverage_tiers
        from mcp_servers.ccxt_server.tools.trading import create_order, cancel_order
        
        self.register_tool(name="get_transaction_history", description="LEDGER: Get Deposits/Withdrawals.", handler=get_transaction_history, parameters={"exchange": {"type": "string"}, "api_key": {"type": "string"}, "secret": {"type": "string"}})
        self.register_tool(name="get_deposit_address", description="LEDGER: Get Deposit Address.", handler=get_deposit_address, parameters={"exchange": {"type": "string"}, "code": {"type": "string"}, "api_key": {"type": "string"}, "secret": {"type": "string"}})
        
        self.register_tool(name="get_borrow_rates", description="MARGIN: Get Borrow Rates.", handler=get_borrow_rates, parameters={"exchange": {"type": "string"}})
        self.register_tool(name="get_leverage_tiers", description="MARGIN: Get Leverage Tiers.", handler=get_leverage_tiers, parameters={"exchange": {"type": "string"}})
        
        self.register_tool(name="create_order", description="TRADING: Create (Buy/Sell) Order. CAUTION.", handler=create_order, parameters={"exchange": {"type": "string"}, "symbol": {"type": "string"}, "side": {"type": "string"}, "type": {"type": "string"}, "amount": {"type": "string"}, "price": {"type": "string"}, "api_key": {"type": "string"}, "secret": {"type": "string"}})
        self.register_tool(name="cancel_order", description="TRADING: Cancel Order.", handler=cancel_order, parameters={"exchange": {"type": "string"}, "id": {"type": "string"}, "symbol": {"type": "string"}, "api_key": {"type": "string"}, "secret": {"type": "string"}})

        # --- 4. SHORTCUT TOOLS (For Top Exchanges) ---
        # "Prioritize tools... create specific tools"
        top_exchanges = ['binance', 'kraken', 'coinbase', 'okx', 'bybit', 'kucoin', 'gateio', 'bitstamp']
        
        for ex in top_exchanges:
            # Ticker Shortcut
            tool_name = f"get_{ex}_ticker"
            async def ticker_handler(args: dict, e=ex) -> ToolResult:
                args['exchange'] = e
                return await get_ticker(args)
            
            self.register_tool(
                name=tool_name, description=f"SHORTCUT: Get {ex.title()} Ticker.",
                handler=ticker_handler, parameters={"symbol": {"type": "string"}}
            )
            
            # Order Book Shortcut
            tool_name_ob = f"get_{ex}_book"
            async def ob_handler(args: dict, e=ex) -> ToolResult:
                args['exchange'] = e
                return await get_order_book(args)
                
            self.register_tool(
                name=tool_name_ob, description=f"SHORTCUT: Get {ex.title()} Order Book.",
                handler=ob_handler, parameters={"symbol": {"type": "string"}}
            )
            
            # Trades Shortcut
            tool_name_trades = f"get_{ex}_trades"
            async def trades_handler(args: dict, e=ex) -> ToolResult:
                args['exchange'] = e
                return await get_trades(args)
            self.register_tool(name=tool_name_trades, description=f"SHORTCUT: Get {ex.title()} Trades.", handler=trades_handler, parameters={"symbol": {"type": "string"}})
            
            # OHLCV Shortcut
            tool_name_ohlcv = f"get_{ex}_ohlcv"
            async def ohlcv_handler(args: dict, e=ex) -> ToolResult:
                args['exchange'] = e
                return await get_ohlcv(args)
            self.register_tool(name=tool_name_ohlcv, description=f"SHORTCUT: Get {ex.title()} Candles.", handler=ohlcv_handler, parameters={"symbol": {"type": "string"}})
            
            # Funding Shortcut
            tool_name_fund = f"get_{ex}_funding"
            async def fund_handler(args: dict, e=ex) -> ToolResult:
                args['exchange'] = e
                return await get_funding_rate(args)
            self.register_tool(name=tool_name_fund, description=f"SHORTCUT: Get {ex.title()} Funding Rate.", handler=fund_handler, parameters={"symbol": {"type": "string"}})
            
            # History Shortcut (Big Data)
            tool_name_hist = f"download_{ex}_history"
            async def hist_handler(args: dict, e=ex) -> ToolResult:
                args['exchange'] = e
                return await download_history(args)
            self.register_tool(name=tool_name_hist, description=f"SHORTCUT: Download {ex.title()} History (10k+).", handler=hist_handler, parameters={"symbol": {"type": "string"}, "days": {"type": "integer"}})
            
            # Positions Shortcut
            tool_name_pos = f"get_{ex}_positions"
            async def pos_handler(args: dict, e=ex) -> ToolResult:
                args['exchange'] = e
                return await get_positions(args)
            self.register_tool(name=tool_name_pos, description=f"SHORTCUT: Get {ex.title()} Positions (Auth).", handler=pos_handler, parameters={"api_key": {"type": "string"}, "secret": {"type": "string"}})
            
            # Liquidations Shortcut
            tool_name_liq = f"get_{ex}_liquidations"
            async def liq_handler(args: dict, e=ex) -> ToolResult:
                args['exchange'] = e
                return await get_liquidations(args)
            self.register_tool(name=tool_name_liq, description=f"SHORTCUT: Get {ex.title()} Liquidations.", handler=liq_handler, parameters={"symbol": {"type": "string"}})
            
            # Ledger Shortcut
            tool_name_led = f"get_{ex}_ledger"
            async def led_handler(args: dict, e=ex) -> ToolResult:
                args['exchange'] = e
                return await get_transaction_history(args)
            self.register_tool(name=tool_name_led, description=f"SHORTCUT: Get {ex.title()} Ledger (Auth).", handler=led_handler, parameters={"api_key": {"type": "string"}, "secret": {"type": "string"}})
             
            # Trading Shortcut (BUY)
            tool_name_buy = f"buy_on_{ex}"
            async def buy_handler(args: dict, e=ex) -> ToolResult:
                args['exchange'] = e
                args['side'] = 'buy'
                return await create_order(args)
            self.register_tool(name=tool_name_buy, description=f"SHORTCUT: Create BUY Order on {ex.title()}.", handler=buy_handler, parameters={"symbol": {"type": "string"}, "type": {"type": "string"}, "amount": {"type": "string"}, "price": {"type": "string"}, "api_key": {"type": "string"}, "secret": {"type": "string"}})
            
            
        # Generic "List Exchanges"
        async def list_all_exchanges(args: dict) -> ToolResult:
            return ToolResult(content=[TextContent(text=str(ccxt.exchanges))])
            
        self.register_tool(name="list_all_exchanges", description="META: List all supported CCXT exchanges.", handler=list_all_exchanges)

async def main():
    from shared.logging import setup_logging, LogConfig
    setup_logging(LogConfig(level="DEBUG", format="console", service_name="ccxt_server"))
    server = CcxtServer()
    try:
        await server.run()
    finally:
        await ExchangeManager.close_all()

if __name__ == "__main__":
    asyncio.run(main())
