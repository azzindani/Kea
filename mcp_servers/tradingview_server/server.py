
from __future__ import annotations
import asyncio
from shared.mcp.server_base import MCPServer
from shared.mcp.protocol import ToolResult, TextContent
from shared.logging import get_logger

# Tools
from mcp_servers.tradingview_server.tools.ta import (
    get_ta_summary, get_oscillators, get_moving_averages, get_indicators
)
from mcp_servers.tradingview_server.tools.screener import (
    scan_market, get_bulk_data
)

logger = get_logger(__name__)

class TradingViewServer(MCPServer):
    """
    TradingView MCP Server ("The Eye").
    Provides Technical Analysis and Bulk Data Retrieval.
    Target: 50-200 Tools via Dynamic Unrolling.
    """
    
    def __init__(self) -> None:
        super().__init__(name="tradingview_server", version="1.0.0")
        self._register_tools()
        
    def _register_tools(self) -> None:
        """Register tools."""
        
        # --- 1. CORE TA TOOLS ---
        self.reg("get_ta_summary", get_ta_summary, "Get specific Buy/Sell/Hold summary.", 
                 params={"symbol": "str", "screener": "str", "exchange": "str", "interval": "str"})
        
        self.reg("get_oscillators_all", get_oscillators, "Get ALL Oscillator values (RSI, MACD, etc).",
                 params={"symbol": "str", "screener": "str", "exchange": "str", "interval": "str"})
                 
        self.reg("get_ma_all", get_moving_averages, "Get ALL Moving Averages (SMA/EMA).",
                 params={"symbol": "str", "screener": "str", "exchange": "str", "interval": "str"})

        # --- 2. GRANULAR TA (Unrolling for High Definition) ---
        # We explicitly register specific indicators for ease of use
        INDICATORS = [
            "RSI", "MACD", "Stoch.K", "Stoch.D", "CCI", "ADX", "AO", "Mom", "Rec.Stoch.RSI",
            "W%R", "UO", "BBP", "EMA10", "EMA20", "EMA50", "EMA100", "EMA200",
            "SMA10", "SMA20", "SMA50", "SMA100", "SMA200", "Ichimoku.BLine", "VWMA",
            "open", "high", "low", "close", "volume", "change",
            "Pivot.M.Classic.S3", "Pivot.M.Classic.S2", "Pivot.M.Classic.S1", "Pivot.M.Classic.Middle", "Pivot.M.Classic.R1", "Pivot.M.Classic.R2", "Pivot.M.Classic.R3",
            "Pivot.M.Fibonacci.S3", "Pivot.M.Fibonacci.S2", "Pivot.M.Fibonacci.S1", "Pivot.M.Fibonacci.Middle", "Pivot.M.Fibonacci.R1", "Pivot.M.Fibonacci.R2", "Pivot.M.Fibonacci.R3"
        ]
        
        for ind in INDICATORS:
            name = f"get_indicator_{ind.lower().replace('.', '_')}"
            desc = f"Get only {ind} value."
            
            # Closure for specific indicator
            async def handler(args: dict, key=ind) -> ToolResult:
                # Reuse get_indicators logic
                res = await get_indicators(args)
                if res.isError: return res
                try:
                    import json
                    data = json.loads(res.content[0].text)
                    val = data.get(key, "N/A")
                    return ToolResult(content=[TextContent(text=str(val))])
                except: return ToolResult(content=[TextContent(text="N/A")])
                
                            
            self.register_tool(name=name, description=desc, handler=handler, 
                               parameters={"symbol": {"type": "string"}, "screener": {"type": "string"}, "exchange": {"type": "string"}, "interval": {"type": "string"}},
                               required=["symbol"])

        # --- 2.5 PHASE 2: SCREENER FIELD BRIDGE (Fundamentals & Performance) ---
        # "The Multi-Talents" - derived from the Screener API
        
        # A. Fundamentals (30 Tools)
        FUNDAMENTALS = {
            "gross_margin": "gross_margin",
            "operating_margin": "operating_margin", 
            "net_margin": "net_margin",
            "return_on_equity": "return_on_equity",
            "return_on_assets": "return_on_assets",
            "return_on_invested_capital": "return_on_invested_capital",
            "debt_to_equity": "debt_to_equity",
            "current_ratio": "current_ratio",
            "quick_ratio": "quick_ratio",
            "price_earnings": "price_earnings_ttm",
            "price_sales": "price_sales_curr",
            "price_book": "price_book_fq",
            "price_cash_flow": "price_cash_flow_ttm",
            "price_free_cash_flow": "price_free_cash_flow_ttm",
            "earnings_per_share": "earnings_per_share_basic_ttm",
            "dividends_yield": "dividend_yield_recent",
            "dividends_paid": "dividends_paid_fq",
            "revenue_growth": "revenue_growth_yoy",
            "net_income_growth": "net_income_growth_yoy",
            "enterprise_value_ebitda": "enterprise_value_ebitda_ttm",
            "total_revenue": "total_revenue_ttm",
            "net_income": "net_income_ttm",
            "total_debt": "total_debt_fq",
            "total_assets": "total_assets_fq",
            "total_liabilities": "total_liabilities_fq",
            "free_cash_flow": "free_cash_flow_ttm",
            "market_cap": "market_cap_basic",
            "number_of_employees": "number_of_employees",
            "sector": "sector",
            "industry": "industry"
        }

        for fname, fkey in FUNDAMENTALS.items():
            tname = f"get_tv_{fname}"
            tdesc = f"Get {fname.replace('_', ' ').title()} via TradingView."
            
            async def fund_handler(args: dict, k=fkey) -> ToolResult:
                # Use scan_market/fetch logic but for single symbol single col
                from mcp_servers.tradingview_server.tools.screener import TvScreener, json
                ticker = args.get("ticker")
                market = args.get("market", "america")
                
                scr = TvScreener()
                # Use bulk mode for single ticker
                res = scr.fetch(market=market, query={"symbol_list": [ticker]}, columns=[k], range_limit=1)
                
                if res and isinstance(res, list) and not "error" in res[0]:
                    val = res[0].get(k, "N/A")
                    return ToolResult(content=[TextContent(text=str(val))])
                return ToolResult(isError=True, content=[TextContent(text="N/A")])

            self.register_tool(name=tname, description=tdesc, handler=fund_handler,
                               parameters={"ticker": {"type": "string"}, "market": {"type": "string"}}, required=["ticker"])

        # B. Performance (15 Tools)
        PERFORMANCE = {
            "perf_1w": "change|1W",
            "perf_1m": "change|1M",
            "perf_3m": "change|3M",
            "perf_6m": "change|6M",
            "perf_ytd": "change|YTD",
            "perf_1y": "change|1Y",
            "perf_5y": "change|5Y",
            "volatility_week": "volatility_W",
            "volatility_month": "volatility_M",
            "volatility_year": "volatility_D", # D usually implies daily vol over year
            "gap": "gap",
            "volume_change": "volume_change", # Relative Volume
            "average_volume_10d": "average_volume_10d_calc",
            "average_volume_30d": "average_volume_30d_calc",
            "average_volume_90d": "average_volume_90d_calc"
        }

        for pname, pkey in PERFORMANCE.items():
            tname = f"get_{pname}"
            tdesc = f"Get {pname.replace('_', ' ').title()}."
            
            async def perf_handler(args: dict, k=pkey) -> ToolResult:
                from mcp_servers.tradingview_server.tools.screener import TvScreener, json
                ticker = args.get("ticker")
                market = args.get("market", "america")
                scr = TvScreener()
                res = scr.fetch(market=market, query={"symbol_list": [ticker]}, columns=[k], range_limit=1)
                if res and isinstance(res, list) and not "error" in res[0]:
                    val = res[0].get(k, "N/A")
                    return ToolResult(content=[TextContent(text=str(val))])
                return ToolResult(isError=True, content=[TextContent(text="N/A")])

            self.register_tool(name=tname, description=tdesc, handler=perf_handler,
                               parameters={"ticker": {"type": "string"}, "market": {"type": "string"}}, required=["ticker"])

        # --- 3. SCREENER / BULK DATA (The Powerhouse) ---
        
        self.reg("scan_market", scan_market, "BULK: Scan market (Top Gainers, Losers, Oversold).", 
                 params={"market": "str", "limit": "int", "preset": "str"})
                 
        self.reg("get_bulk_data", get_bulk_data, "MULTI-TALENT: Get custom data columns for list of tickers.", 
                 params={"tickers": "list", "columns": "list", "market": "str"})

        # --- 4. PRESET SCANNERS (Convenience) ---
        PRESETS = ["top_gainers", "top_losers", "most_active", "oversold", "overbought"]
        MARKETS = ["america", "indonesia", "crypto", "forex"]
        
        for m in MARKETS:
            for p in PRESETS:
                t_name = f"scan_{m}_{p}"
                t_desc = f"Quick Scan: {p.replace('_', ' ').title()} in {m.title()}"
                
                async def p_handler(args: dict, mkt=m, pre=p) -> ToolResult:
                    return await scan_market({"market": mkt, "preset": pre, "limit": args.get("limit", 50)})
                
                self.register_tool(name=t_name, description=t_desc, handler=p_handler,
                                   parameters={"limit": {"type": "integer", "description": "Max results"}}, required=[])

    def reg(self, name, handler, desc, params=None):
        if params is None:
            p = {}
            r = []
        else:
            p = {}
            r = []
            for k, v in params.items():
                p[k] = {"type": "string" if v == "str" else ("integer" if v == "int" else "array")}
                r.append(k)
        self.register_tool(name=name, description=desc, handler=handler, parameters=p, required=r)

async def main():
    from shared.logging import setup_logging, LogConfig
    setup_logging(LogConfig(level="DEBUG", format="console", service_name="tradingview_server"))
    server = TradingViewServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
