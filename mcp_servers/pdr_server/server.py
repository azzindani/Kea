from __future__ import annotations

import sys
from pathlib import Path
# Fix for importing 'shared' module from root when running in JIT mode
root_path = str(Path(__file__).parents[2])
if root_path not in sys.path:
    sys.path.append(root_path)

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
import asyncio
from mcp.server.fastmcp import FastMCP

# --- PATCH: Fix pandas-datareader compatibility ---
# pandas-datareader uses an old signature for deprecate_kwarg.
# We patch it to prevent TypeError on import.
try:
    import pandas.util._decorators
    def mock_deprecate_kwarg(old_arg_name, new_arg_name, mapping=None, stacklevel=2):
        def decorator(func):
            return func
        return decorator
    pandas.util._decorators.deprecate_kwarg = mock_deprecate_kwarg
except ImportError:
    pass
# --------------------------------------------------

# Tools - use aliased imports to avoid naming collisions
from tools import famafrench, market_global, dashboards, market_symbols, central_bank, commercial

mcp = FastMCP("pdr_server", dependencies=["pandas_datareader", "pandas"])

# --- 1. ACADEMIC ENGINE (Fama-French) ---

@mcp.tool()
async def get_fama_french_data(dataset_name: str, start_date: str = None, end_date: str = None) -> str:
    """
    ACADEMIC: Get Fama-French Data by Code.
    Common Codes: 'F-F_Research_Data_Factors', 'F-F_Momentum_Factor', '5_Industry_Portfolios'.
    """
    return await famafrench.get_fama_french_data(dataset_name, start_date, end_date)

# --- 2. MARKET ENGINE (Stooq, TSP) ---

@mcp.tool()
async def get_stooq_data(symbols: list[str], start_date: str = None) -> str:
    """MARKET: Stooq Data (Indices, Bonds, Commodities)."""
    return await market_global.get_stooq_data(symbols, start_date)

@mcp.tool()
async def get_tsp_fund_data() -> str:
    """INSTITUTION: Thrift Savings Plan (TSP) Funds."""
    return await market_global.get_tsp_fund_data()

@mcp.tool()
async def get_moex_data(symbols: list[str], start_date: str = None) -> str:
    """MARKET: Moscow Exchange Data."""
    return await market_global.get_moex_data(symbols, start_date)

# --- 3. DASHBOARDS ---

@mcp.tool()
async def get_factor_dashboard() -> str:
    """DASHBOARD: US Factors (5-Factor + Momentum)."""
    return await dashboards.get_factor_dashboard()

@mcp.tool()
async def get_global_factors_dashboard() -> str:
    """DASHBOARD: Global Factors (Regions)."""
    return await dashboards.get_global_factors_dashboard()

@mcp.tool()
async def get_industry_health_dashboard() -> str:
    """DASHBOARD: 49 Industry Sectors Health."""
    return await dashboards.get_industry_health_dashboard()

@mcp.tool()
async def get_liquidity_dashboard() -> str:
    """DASHBOARD: Market Liquidity Factors."""
    return await dashboards.get_liquidity_dashboard()

# --- 4. DISCOVERY & CENTRAL BANK ---

@mcp.tool()
async def get_nasdaq_symbol_list(query: str = None) -> str:
    """DISCOVERY: Search Nasdaq/NYSE Symbols."""
    return await market_symbols.get_nasdaq_symbol_list(query)

@mcp.tool()
async def get_bank_of_canada_data(symbols: list[str] = None, start_date: str = None) -> str:
    """MACRO: Bank of Canada Rates/FX."""
    return await central_bank.get_bank_of_canada_data(symbols, start_date)

# --- 5. COMMERCIAL ---

@mcp.tool()
async def get_tiingo_data(symbols: list[str], api_key: str = None, start_date: str = None) -> str:
    """COMMERCIAL: Tiingo Data (Req API Key)."""
    return await commercial.get_tiingo_data(symbols, api_key, start_date)

@mcp.tool()
async def get_alphavantage_data(symbols: list[str], api_key: str = None, start_date: str = None) -> str:
    """COMMERCIAL: AlphaVantage Data (Req API Key)."""
    return await commercial.get_alphavantage_data(symbols, api_key, start_date)


if __name__ == "__main__":
    mcp.run()