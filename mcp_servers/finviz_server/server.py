
from __future__ import annotations
import asyncio
from shared.mcp.server_base import MCPServer
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

# Tools
from mcp_servers.finviz_server.tools.screener import get_screener_signal, get_signal_map
from mcp_servers.finviz_server.tools.quote import get_stock_depth
from mcp_servers.finviz_server.tools.groups import get_group_data
from mcp_servers.finviz_server.tools.insider import get_insider_market

logger = get_logger(__name__)

class FinvizServer(MCPServer):
    """
    Finviz MCP Server.
    Focus: Screening, Signals, and Visual Sentiment.
    """
    
    def __init__(self) -> None:
        super().__init__(name="finviz_server", version="1.0.0")
        self._register_tools()
        
    def _register_tools(self) -> None:
        
        # --- 1. SCREENER TOOLS (Dynamic Unrolling of Signals) ---
        # 27+ Tools
        
        SIGNALS = get_signal_map()
        
        for key, nice_name in SIGNALS.items():
            name = f"screen_{key}"
            desc = f"SIGNAL: Get stocks matching '{nice_name}'."
            
            async def scr_handler(args: dict, k=key) -> ToolResult:
                args["signal"] = k
                return await get_screener_signal(args)
                
            self.register_tool(
                name=name, description=desc, handler=scr_handler,
                parameters={"limit": {"type": "integer", "description": "Max results (default 30)"}}
            )

        # --- 2. QUOTE TOOLS (Ticker Depth) ---
        # 5 Tools
        
        modes = [
            ("description", "Get company description."),
            ("ratings", "Get analyst ratings (Upgrades/Downgrades)."),
            ("news", "Get latest news headlines for ticker."),
            ("insider", "Get insider trading for this ticker."),
            ("fundament", "Get fundamental ratios (P/E, EPS, etc).")
        ]
        
        for m, d in modes:
            name = f"get_stock_{m}"
            desc = f"QUOTE: {d}"
            
            async def q_handler(args: dict, mode=m) -> ToolResult:
                return await get_stock_depth(args, mode)
                
            self.register_tool(
                name=name, description=desc, handler=q_handler,
                parameters={"ticker": {"type": "string"}}, required=["ticker"]
            )

        # --- 3. GROUPS TOOLS (Market Map) ---
        # 3 major modes x 3 groups = 9 Tools
        
        groups = ["Sector", "Industry", "Country"]
        views = ["overview", "valuation", "performance"]
        
        for g in groups:
            for v in views:
                name = f"get_{g.lower()}_{v}"
                desc = f"GROUP: Get {g} {v} table."
                
                async def g_handler(args: dict, grp=g, view=v) -> ToolResult:
                    args["group_by"] = grp
                    return await get_group_data(args, view)
                    
                self.register_tool(name=name, description=desc, handler=g_handler)

        # --- 4. INSIDER TOOLS (Market Flow) ---
        # 6 Tools
        
        insider_opts = [
            "latest_buys", "latest_sales", 
            "top_week_buys", "top_week_sales",
            "top_owner_buys", "top_owner_sales"
        ]
        
        for opt in insider_opts:
            name = f"get_{opt}"
            desc = f"INSIDER: Get {opt.replace('_', ' ')}."
            
            async def i_handler(args: dict, o=opt) -> ToolResult:
                args["subset"] = o
                return await get_insider_market(args)
            
            self.register_tool(name=name, description=desc, handler=i_handler)

        # --- 5. PHASE 2: GLOBAL MARKETS ---
        
        from mcp_servers.finviz_server.tools.global_markets import get_global_performance
        
        self.register_tool(
            name="get_forex_performance", description="GLOBAL: Get Forex performance table.",
            handler=lambda args: get_global_performance(args, "forex")
        )
        self.register_tool(
            name="get_crypto_performance", description="GLOBAL: Get Crypto performance table.",
            handler=lambda args: get_global_performance(args, "crypto")
        )

        # --- 6. PHASE 2: CALENDAR & NEWS ---
        
        from mcp_servers.finviz_server.tools.calendar_news import get_earnings_calendar, get_market_news
        
        self.register_tool(
            name="get_earnings_calendar", description="CALENDAR: Get Earnings for 'This Week', 'Next Week', etc.",
            handler=get_earnings_calendar, parameters={"period": {"type": "string"}}
        )
        
        self.register_tool(
            name="get_market_news", description="NEWS: Get General Market News or Blogs.",
            handler=get_market_news, parameters={"mode": {"type": "string"}}
        )

        # --- 7. PHASE 2: STRATEGY PRESETS ---
        
        from mcp_servers.finviz_server.tools.strategy import get_strategy_screen, PRESETS
        
        for strat in PRESETS:
            name = f"screen_strat_{strat}"
            desc = f"STRATEGY: Screen for '{strat.replace('_', ' ').title()}'."
            
            async def s_handler(args: dict, s=strat) -> ToolResult:
                args["strategy"] = s
                return await get_strategy_screen(args)
                
            self.register_tool(name=name, description=desc, handler=s_handler)

        # --- 8. PHASE 3: DEEP EXPANSION (Charts, Financials, TA) ---
        
        from mcp_servers.finviz_server.tools.charts import get_chart_url
        from mcp_servers.finviz_server.tools.financials import get_finviz_statement
        from mcp_servers.finviz_server.tools.bulk_ta import get_technical_table
        
        self.register_tool(
            name="get_chart_url", description="CHART: Get Finviz Chart image URL.",
            handler=get_chart_url, parameters={"ticker": {"type": "string"}}
        )
        
        self.register_tool(
            name="get_finviz_statement", description="FINANCIALS: Get Income/Balance/Cash Flow table.",
            handler=get_finviz_statement, parameters={"ticker": {"type": "string"}, "statement": {"type": "string"}}
        )
        
        self.register_tool(
            name="get_technical_table", description="TA: Get Bulk Technical Indicators (RSI, SMA, ATR).",
            handler=get_technical_table, parameters={"limit": {"type": "integer"}}
        )

async def main():
    from shared.logging import setup_logging, LogConfig
    setup_logging(LogConfig(level="DEBUG", format="console", service_name="finviz_server"))
    server = FinvizServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
