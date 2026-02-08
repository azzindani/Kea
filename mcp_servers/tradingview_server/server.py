
import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)


from mcp.server.fastmcp import FastMCP
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from tools import ta, screener as screener_module
import structlog
import json

logger = structlog.get_logger()

# Create the FastMCP server
from shared.logging import setup_logging
setup_logging()

mcp = FastMCP("tradingview_server", dependencies=["tradingview_ta", "requests"])

# --- 1. CORE TA TOOLS ---

@mcp.tool()
async def get_ta_summary(symbol: str, market: str = "america", exchange: str = "NASDAQ", interval: str = "1d") -> str:
    """FETCHES TA summary. [ACTION]
    
    [RAG Context]
    Get high-level Technical Analysis Summary (Buy/Sell/Hold).
    Returns JSON summary.
    """
    return await ta.get_ta_summary(symbol, market, exchange, interval)

@mcp.tool()
async def get_oscillators_all(symbol: str, market: str = "america", exchange: str = "NASDAQ", interval: str = "1d") -> str:
    """FETCHES all oscillators. [ACTION]
    
    [RAG Context]
    Get ALL Oscillator values (RSI, MACD, etc).
    Returns JSON string.
    """
    return await ta.get_oscillators(symbol, market, exchange, interval)

@mcp.tool()
async def get_ma_all(symbol: str, market: str = "america", exchange: str = "NASDAQ", interval: str = "1d") -> str:
    """FETCHES all moving averages. [ACTION]
    
    [RAG Context]
    Get ALL Moving Averages (SMA/EMA).
    Returns JSON string.
    """
    return await ta.get_moving_averages(symbol, market, exchange, interval)

# --- 2. GRANULAR TA (Unrolling for High Definition) ---
# We explicitly register specific indicators for ease of use
INDICATORS = [
    "RSI", "MACD", "Stoch.K", "Stoch.D", "CCI", "ADX", "AO", "Mom", "Rec.Stoch.RSI",
    "W_R", "UO", "BBP", "EMA10", "EMA20", "EMA50", "EMA100", "EMA200",
    "SMA10", "SMA20", "SMA50", "SMA100", "SMA200", "Ichimoku.BLine", "VWMA",
    "open", "high", "low", "close", "volume", "change",
    "Pivot.M.Classic.S3", "Pivot.M.Classic.S2", "Pivot.M.Classic.S1", "Pivot.M.Classic.Middle", "Pivot.M.Classic.R1", "Pivot.M.Classic.R2", "Pivot.M.Classic.R3",
    "Pivot.M.Fibonacci.S3", "Pivot.M.Fibonacci.S2", "Pivot.M.Fibonacci.S1", "Pivot.M.Fibonacci.Middle", "Pivot.M.Fibonacci.R1", "Pivot.M.Fibonacci.R2", "Pivot.M.Fibonacci.R3"
]

def register_indicators():
    # Loop removed as it was shadowing the loop below
        
    def make_handler(ind_name):
        async def handler(symbol: str, market: str = "america", exchange: str = "NASDAQ", interval: str = "1d") -> str:
            # Reuse get_indicators logic
            res_str = await ta.get_indicators(symbol, market, exchange, interval)
            try:
                if res_str.startswith("Error"): return res_str
                data = json.loads(res_str)
                # Use captured variable
                val = data.get(ind_name, "N/A")
                return str(val)
            except: 
                return "N/A"
        return handler

    for ind in INDICATORS:
        name = f"get_indicator_{ind.lower().replace('.', '_')}"
        # Enhanced Docstring
        desc = f"FETCHES {ind} value. [ACTION]\n\n[RAG Context]\nGet only {ind} value from TradingView."
        
        mcp.add_tool(
            name=name,
            description=desc,
            fn=make_handler(ind)
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
    # Loop removed as it was shadowing the loop below
        
    def make_fund_handler(fkey):
        async def fund_handler(ticker: str, market: str = "america") -> str:
            scr = screener_module.TvScreener()
            # Use bulk mode for single ticker
            res = scr.fetch(market=market, query={"symbol_list": [ticker]}, columns=[fkey], range_limit=1)
            
            if res and isinstance(res, list) and not "error" in res[0]:
                val = res[0].get(fkey, "N/A")
                return str(val)
            return "N/A"
        return fund_handler

    for fname, fkey in FUNDAMENTALS.items():
        tname = f"get_tv_{fname}"
        # Enhanced Docstring
        tdesc = f"FETCHES {fname.replace('_', ' ').title()}. [ACTION]\n\n[RAG Context]\nGet {fname} fundamental data via TradingView."
        
        mcp.add_tool(name=tname, description=tdesc, fn=make_fund_handler(fkey))
    
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
    # Loop removed as it was shadowing the loop below
        
    def make_perf_handler(pkey):
        async def perf_handler(ticker: str, market: str = "america") -> str:
            scr = screener_module.TvScreener()
            res = scr.fetch(market=market, query={"symbol_list": [ticker]}, columns=[pkey], range_limit=1)
            if res and isinstance(res, list) and not "error" in res[0]:
                val = res[0].get(pkey, "N/A")
                return str(val)
            return "N/A"
        return perf_handler

    for pname, pkey in PERFORMANCE.items():
        tname = f"get_{pname}"
        # Enhanced Docstring
        tdesc = f"FETCHES {pname.replace('_', ' ').title()}. [ACTION]\n\n[RAG Context]\nGet {pname} performance metric."
        
        mcp.add_tool(name=tname, description=tdesc, fn=make_perf_handler(pkey))

register_performance()

# --- 3. SCREENER / BULK DATA ---

@mcp.tool()
async def scan_market(market: str = "america", limit: int = 100000, preset: str = "market_cap") -> str:
    """SCANS market using preset. [ACTION]
    
    [RAG Context]
    Scan market with presets (Top Gainers, Losers, Oversold).
    Returns JSON list of tickers.
    """
    return await screener_module.scan_market(market, limit, preset)

@mcp.tool()
async def get_bulk_data(tickers: list[str], columns: list[str] = None, market: str = "america") -> str:
    """FETCHES bulk data. [ACTION]
    
    [RAG Context]
    Get custom data columns for list of tickers (Multi-Talent).
    Returns JSON string of data.
    """
    return await screener_module.get_bulk_data(tickers, columns, market)

# --- 4. PRESET SCANNERS (Convenience) ---
PRESETS = ["top_gainers", "top_losers", "most_active", "oversold", "overbought"]
MARKETS = ["america", "indonesia", "crypto", "forex"]

def register_presets():
    # Loop removed as it was shadowing the loop below
            
    def make_preset_handler(m_val, p_val):
        async def p_handler(limit: int = 100000) -> str:
            return await screener_module.scan_market(m_val, limit, p_val)
        return p_handler

    for m in MARKETS:
        for p in PRESETS:
            t_name = f"scan_{m}_{p}"
            # Enhanced Docstring
            t_desc = f"SCANS {p.replace('_', ' ').title()} in {m.title()}. [ACTION]\n\n[RAG Context]\nQuick Preset Scan."
             
            mcp.add_tool(name=t_name, description=t_desc, fn=make_preset_handler(m, p))

register_presets()

if __name__ == "__main__":
    mcp.run()