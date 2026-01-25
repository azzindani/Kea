
from __future__ import annotations
import asyncio
from shared.mcp.server_base import MCPServer
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

# Tools
from mcp_servers.yahooquery_server.tools.ticker import (
    generic_ticker_handler, get_fundamental_snapshot
)
from mcp_servers.yahooquery_server.tools.screener import get_screen_data
from mcp_servers.yahooquery_server.tools.analysis import get_history_bulk

logger = get_logger(__name__)

class YahooQueryServer(MCPServer):
    """
    YahooQuery MCP Server ("The Bulk Factory").
    Focuses on retrieving data for MULTIPLE tickers simultaneously.
    """
    
    def __init__(self) -> None:
        super().__init__(name="yahooquery_server", version="1.0.0")
        self._register_tools()
        
    def _register_tools(self) -> None:
        
        # --- 1. TICKER ATTRIBUTE TOOLS (Dynamic Unrolling) ---
        # These tools accept a LIST of tickers and return data for ALL of them.
        
        MODULES = [
            "asset_profile", "calendar_events", "company_officers", "earning_history",
            "earnings", "earnings_trend", "esg_scores", "financial_data",
            "fund_bond_holdings", "fund_bond_ratings", "fund_equity_holdings",
            "fund_holding_info", "fund_ownership", "fund_performance", "fund_profile",
            "fund_sector_weightings", "fund_top_holdings", "grading_history",
            "index_trend", "industry_trend", "insider_holders", "insider_transactions",
            "institution_ownership", "key_stats", "major_holders", "page_views",
            "price", "quote_type", "recommendation_trend", "sec_filings",
            "share_purchase_activity", "summary_detail", "summary_profile"
        ]
        
        for mod in MODULES:
            name = f"get_bulk_{mod}"
            desc = f"BULK: Get {mod.replace('_', ' ').title()} for multiple tickers."
            
            # Closure
            async def handler(args: dict, m=mod) -> ToolResult:
                return await generic_ticker_handler(args, m)
            
            self.register_tool(
                name=name, description=desc, handler=handler,
                parameters={"tickers": {"type": "array", "items": {"type": "string"}, "description": "List of symbols (e.g. ['AAPL', 'MSFT'])"}},
                required=["tickers"]
            )

        # --- 2. MULTI-TALENT AGGREGATORS ---
        
        from mcp_servers.yahooquery_server.tools.ticker import (
            get_fundamental_snapshot, get_ownership_report, 
            get_earnings_report, get_technical_snapshot
        )

        AGGS = [
            ("get_fundamental_snapshot", get_fundamental_snapshot, "MULTI-TALENT: Get Price, Key Stats, and Summary."),
            ("get_ownership_report", get_ownership_report, "MULTI-TALENT: Major Holders, Insiders, Institutions."),
            ("get_earnings_report", get_earnings_report, "MULTI-TALENT: Earnings history, trend, and calendar."),
            ("get_technical_snapshot", get_technical_snapshot, "MULTI-TALENT: Price, Recs, and Trends.")
        ]
        
        for name, handler, desc in AGGS:
            self.register_tool(
                name=name, description=desc, handler=handler,
                parameters={"tickers": {"type": "array"}}, required=["tickers"]
            )

        # --- 3. SCREENER TOOLS ---
        
        PRESETS = [
            "day_gainers", "day_losers", "most_actives", "cryptocurrencies",
            "undervalued_growth_stocks", "technology_stocks", "growth_technology_stocks",
            "undervalued_large_caps", "aggressive_small_caps", "small_cap_gainers",
            "top_mutual_funds", "portfolio_anchors", "solid_large_caps"
        ]
        
        for preset in PRESETS:
            name = f"screen_{preset}"
            desc = f"SCREEN: Get {preset.replace('_', ' ').title()}."
            
            async def scr_handler(args: dict, p=preset) -> ToolResult:
                # Inject preset into args
                args["preset"] = p
                return await get_screen_data(args)
                
            self.register_tool(
                name=name, description=desc, handler=scr_handler,
                parameters={"count": {"type": "integer", "description": "Number of results (default 25)"}}
            )

        # --- 4. HISTORY ---
        
        self.register_tool(
            name="get_history_bulk",
            description="BULK: Download historical price data for multiple tickers.",
            handler=get_history_bulk,
            parameters={"tickers": {"type": "array"}, "period": {"type": "string"}, "interval": {"type": "string"}},
            required=["tickers"]
        )

        # --- 5. PHASE 2: FINANCIAL STATEMENTS (Deep Data) ---
        
        from mcp_servers.yahooquery_server.tools.ticker import get_bulk_financials_handler
        
        FINANCIALS = ["balance_sheet", "cash_flow", "income_statement"]
        
        for fin in FINANCIALS:
            # Annual
            name_a = f"get_bulk_{fin}_annual"
            desc_a = f"BULK: Get Annual {fin.replace('_', ' ').title()}."
            async def handler_a(args: dict, m=fin) -> ToolResult:
                args["frequency"] = "a"
                return await get_bulk_financials_handler(args, m)
                
            self.register_tool(name=name_a, description=desc_a, handler=handler_a, parameters={"tickers": {"type": "array"}}, required=["tickers"])
            
            # Quarterly
            name_q = f"get_bulk_{fin}_quarterly"
            desc_q = f"BULK: Get Quarterly {fin.replace('_', ' ').title()}."
            async def handler_q(args: dict, m=fin) -> ToolResult:
                args["frequency"] = "q"
                return await get_bulk_financials_handler(args, m)
                
            self.register_tool(name=name_q, description=desc_q, handler=handler_q, parameters={"tickers": {"type": "array"}}, required=["tickers"])

        # --- 6. PHASE 2: OPTIONS ENGINE ---
        
        from mcp_servers.yahooquery_server.tools.ticker import get_bulk_options_handler
        
        self.register_tool(
            name="get_bulk_option_chain",
            description="BULK: Get Option Chain (Top 100 rows) for multiple tickers.",
            handler=get_bulk_options_handler,
            parameters={"tickers": {"type": "array"}},
            required=["tickers"]
        )

        # --- 7. PHASE 2: MARKET INTELLIGENCE ---
        
        from mcp_servers.yahooquery_server.tools.market_intelligence import get_market_trending
        
        self.register_tool(
            name="get_market_trending",
            description="INTEL: Get trending securities by country (e.g. US, ID).",
            handler=get_market_trending,
            parameters={"country": {"type": "string"}, "count": {"type": "integer"}}
        )

        # --- 8. PHASE 3: MASSIVE SCREENER EXPANSION (Sector & Funds) ---
        
        # Sector / Industry Specifics
        SECTORS = [
            "ms_basic_materials", "ms_communication_services", "ms_consumer_cyclical",
            "ms_consumer_defensive", "ms_energy", "ms_financial_services",
            "ms_healthcare", "ms_industrials", "ms_real_estate", 
            "ms_technology", "ms_utilities"
        ]
        
        for sect in SECTORS:
            # Clean name: ms_basic_materials -> screen_sector_basic_materials
            clean_name = sect.replace("ms_", "sector_")
            name = f"screen_{clean_name}"
            desc = f"SCREEN: Get {clean_name.replace('_', ' ').title()} stocks."
            
            async def h(args: dict, p=sect) -> ToolResult:
                args["preset"] = p
                return await get_screen_data(args)
            
            self.register_tool(name=name, description=desc, handler=h, parameters={"count": {"type": "integer"}})

        # Funds & specialized lists
        SPECIAL_LISTS = [
            "conservative_foreign_funds", "growth_technology_stocks", "high_yield_bond",
            "most_shorted_stocks", "undervalued_large_caps", "undervalued_growth_stocks",
            "aggressive_small_caps", "portfolio_anchors", "small_cap_gainers"
        ]
        
        for sl in SPECIAL_LISTS:
            name = f"screen_{sl}"
            desc = f"SCREEN: Get {sl.replace('_', ' ').title()}."
            async def h_sl(args: dict, p=sl) -> ToolResult:
                args["preset"] = p
                return await get_screen_data(args)
            self.register_tool(name=name, description=desc, handler=h_sl, parameters={"count": {"type": "integer"}})

        # --- 9. PHASE 4: UNIVERSAL ASSETS (Funds & Discovery) ---
        
        from mcp_servers.yahooquery_server.tools.funds_and_discovery import (
            get_fund_holdings_formatted, get_fund_sector_weightings,
            search_instruments, get_ticker_news
        )

        self.register_tool(
            name="get_fund_holdings",
            description="FUND: Get Top Holdings Table (Equity/Bond/Position).",
            handler=get_fund_holdings_formatted, parameters={"tickers": {"type": "array"}}, required=["tickers"]
        )
        
        self.register_tool(
            name="get_fund_sector_weightings",
            description="FUND: Get Sector Weightings Table.",
            handler=get_fund_sector_weightings, parameters={"tickers": {"type": "array"}}, required=["tickers"]
        )
        
        self.register_tool(
            name="search_instruments",
            description="DISCOVERY: Search for ANY instrument (Gold, Bitcoin, Bonds).",
            handler=search_instruments, parameters={"query": {"type": "string"}}, required=["query"]
        )
        
        self.register_tool(
            name="get_ticker_news",
            description="NEWS: Get latest news for tickers.",
            handler=get_ticker_news, parameters={"tickers": {"type": "array"}}, required=["tickers"]
        )

async def main():
    from shared.logging import setup_logging, LogConfig
    setup_logging(LogConfig(level="DEBUG", format="console", service_name="yahooquery_server"))
    server = YahooQueryServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
