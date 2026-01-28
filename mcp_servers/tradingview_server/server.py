from mcp.server.fastmcp import FastMCP
from mcp_servers.tradingview_server.tools import ta, screener
import structlog
import json

logger = structlog.get_logger()

# Create the FastMCP server
mcp = FastMCP("tradingview_server", dependencies=["tradingview_ta", "requests"])

# --- 1. CORE TA TOOLS ---

@mcp.tool()
async def get_ta_summary(symbol: str, screener: str = "america", exchange: str = "NASDAQ", interval: str = "1d") -> str:
    """Get high-level Technical Analysis Summary (Buy/Sell/Hold)."""
    return await ta.get_ta_summary(symbol, screener, exchange, interval)

@mcp.tool()
async def get_oscillators_all(symbol: str, screener: str = "america", exchange: str = "NASDAQ", interval: str = "1d") -> str:
    """Get ALL Oscillator values (RSI, MACD, etc)."""
    return await ta.get_oscillators(symbol, screener, exchange, interval)

@mcp.tool()
async def get_ma_all(symbol: str, screener: str = "america", exchange: str = "NASDAQ", interval: str = "1d") -> str:
    """Get ALL Moving Averages (SMA/EMA)."""
    return await ta.get_moving_averages(symbol, screener, exchange, interval)

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

def register_indicators():
    for ind in INDICATORS:
        name = f"get_indicator_{ind.lower().replace('.', '_')}"
        desc = f"Get only {ind} value."
        
        # Closure for specific indicator
        async def handler(symbol: str, screener: str = "america", exchange: str = "NASDAQ", interval: str = "1d", _key=ind) -> str:
            # Reuse get_indicators logic
            res_str = await ta.get_indicators(symbol, screener, exchange, interval)
            try:
                if res_str.startswith("Error"): return res_str
                data = json.loads(res_str)
                val = data.get(_key, "N/A")
                return str(val)
            except: 
                return "N/A"
        
        mcp.add_tool(
            name=name,
            description=desc,
            fn=handler
        )

register_indicators()

# --- 2.5 PHASE 2: SCREENER FIELD BRIDGE (Fundamentals & Performance) ---
# "The Multi-Talents" - derived from the Screener API

# A. Fundamentals
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

def register_fundamentals():
    for fname, fkey in FUNDAMENTALS.items():
        tname = f"get_tv_{fname}"
        tdesc = f"Get {fname.replace('_', ' ').title()} via TradingView."
        
        async def fund_handler(ticker: str, market: str = "america", _k=fkey) -> str:
            from mcp_servers.tradingview_server.tools.screener import TvScreener
            scr = TvScreener()
            # Use bulk mode for single ticker
            res = scr.fetch(market=market, query={"symbol_list": [ticker]}, columns=[_k], range_limit=1)
            
            if res and isinstance(res, list) and not "error" in res[0]:
                val = res[0].get(_k, "N/A")
                return str(val)
            return "N/A"

        mcp.add_tool(name=tname, description=tdesc, fn=fund_handler)

register_fundamentals()

# B. Performance
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
    "volatility_year": "volatility_D",
    "gap": "gap",
    "volume_change": "volume_change", # Relative Volume
    "average_volume_10d": "average_volume_10d_calc",
    "average_volume_30d": "average_volume_30d_calc",
    "average_volume_90d": "average_volume_90d_calc"
}

def register_performance():
    for pname, pkey in PERFORMANCE.items():
        tname = f"get_{pname}"
        tdesc = f"Get {pname.replace('_', ' ').title()}."
        
        async def perf_handler(ticker: str, market: str = "america", _k=pkey) -> str:
            from mcp_servers.tradingview_server.tools.screener import TvScreener
            scr = TvScreener()
            res = scr.fetch(market=market, query={"symbol_list": [ticker]}, columns=[_k], range_limit=1)
            if res and isinstance(res, list) and not "error" in res[0]:
                val = res[0].get(_k, "N/A")
                return str(val)
            return "N/A"

        mcp.add_tool(name=tname, description=tdesc, fn=perf_handler)

register_performance()

# --- 3. SCREENER / BULK DATA ---

@mcp.tool()
async def scan_market(market: str = "america", limit: int = 100000, preset: str = "market_cap") -> str:
    """BULK: Scan market (Top Gainers, Losers, Oversold)."""
    return await screener.scan_market(market, limit, preset)

@mcp.tool()
async def get_bulk_data(tickers: list[str], columns: list[str] = None, market: str = "america") -> str:
    """MULTI-TALENT: Get custom data columns for list of tickers."""
    return await screener.get_bulk_data(tickers, columns, market)

# --- 4. PRESET SCANNERS (Convenience) ---
PRESETS = ["top_gainers", "top_losers", "most_active", "oversold", "overbought"]
MARKETS = ["america", "indonesia", "crypto", "forex"]

def register_presets():
    for m in MARKETS:
        for p in PRESETS:
            t_name = f"scan_{m}_{p}"
            t_desc = f"Quick Scan: {p.replace('_', ' ').title()} in {m.title()}"
            
            async def p_handler(limit: int = 100000, _m=m, _p=p) -> str:
                return await scan_market(_m, limit, _p)
            
            mcp.add_tool(name=t_name, description=t_desc, fn=p_handler)

register_presets()

if __name__ == "__main__":
    mcp.run()
