
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
